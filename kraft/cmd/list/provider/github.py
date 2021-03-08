# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Europe Laboratories GmbH., NEC Corporation.
#                     All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# flake8: noqa
from __future__ import absolute_import
from __future__ import unicode_literals

import fnmatch
import os
import re
import threading
from queue import Queue
from urllib.parse import urlparse

import click
from github import Github
from github.Repository import Repository

from .git import GitListProvider
from .tarball import TarballListProvider
from kraft.const import GIT_UNIKRAFT_TAG_PATTERN
from kraft.const import GITHUB_ORIGIN
from kraft.const import GITHUB_TARBALL
from kraft.const import UNIKRAFT_RELEASE_STABLE
from kraft.logger import logger
from kraft.types import break_component_naming_format
from kraft.util import ErrorPropagatingThread


class GitHubListProvider(GitListProvider):
    @classmethod
    def is_type(cls, origin=None):
        if origin is None:
            return False

        uri = urlparse(origin)
        if uri.netloc == GITHUB_ORIGIN:
            github_org = uri.path.split('/')[1]

            if "*" in github_org:
                logger.warn("Cannot use wildcard in GitHub organisation names!")
                return False

            return True

        return False

    @click.pass_context
    def probe(ctx, self, origin=None, items=None, return_threads=False):
        # TODO: There should be a work around to fix this import loop cycle
        from kraft.manifest import Manifest

        if self.is_type(origin) is False:
            return []

        threads = list()
        if items is None:
            items = Queue()

        manifest = ctx.obj.cache.get(origin)

        if manifest is None:
            manifest = Manifest(
                manifest=origin
            )

        uri = urlparse(origin)

        # Is the origin from GitHub?
        if uri.netloc == GITHUB_ORIGIN:
            github_api = Github(ctx.obj.env.get('UK_KRAFT_GITHUB_TOKEN', None))
            github_org = uri.path.split('/')[1]
            github_repo = uri.path.split('/')[2]

            if "*" in github_org:
                logger.warn("Cannot use wildcard in GitHub organisation names!")
                return

            # Does the origin contain a wildcard in the repo name?
            if "*" in github_repo:
                logger.info("Populating via wildcard: %s" % origin)

                org = github_api.get_organization(github_org)
                repos = org.get_repos()

                for repo in repos:
                    if return_threads:
                        thread = ErrorPropagatingThread(
                            target=lambda *arg: items.put(get_component_from_github(*arg)),
                            args=(
                                ctx,
                                origin,
                                github_org,
                                repo.name,
                            )
                        )
                        threads.append(thread)
                        thread.start()
                    else:
                        items.put(get_component_from_github(
                            ctx,
                            origin,
                            github_org,
                            repo.name
                        ))
            else:
                logger.info("Using direct repository: %s" % origin)

                if return_threads:
                    thread = ErrorPropagatingThread(
                        target=lambda *arg: items.put(get_component_from_github(*arg)),
                        args=(
                            ctx,
                            origin,
                            github_org,
                            github_repo,
                        )
                    )
                    threads.append(thread)
                    thread.start()
                else:
                    items.put(get_component_from_github(
                        ctx,
                        origin,
                        github_org,
                        github_repo
                    ))

        return items, threads

    @click.pass_context
    def download(ctx, self, manifest=None, localdir=None, version=None,
            override_existing=False, use_git=False):
        # TODO: Fix Tarball downloader
        use_git = True
        provider = (GitListProvider if use_git else TarballListProvider)()
        provider.download(
            manifest=manifest,
            localdir=localdir,
            version=version,
            override_existing=override_existing
        )


def get_component_from_github(ctx, origin=None, org=None, repo=None):
    if origin is None:
        raise ValueError("expected origin")
    elif org is None:
        raise ValueError("expected org")
    elif repo is None:
        raise ValueError("expected repo")

    # TODO: There should be a work around to fix this import loop cycle
    from kraft.manifest import ManifestItem
    from kraft.manifest import ManifestItemVersion
    from kraft.manifest import ManifestItemDistribution
    from .types import ListProviderType

    if isinstance(repo, str):
        if ".git" in repo:
            repo = repo.split(".")[0]
        github_api = Github(ctx.obj.env.get('UK_KRAFT_GITHUB_TOKEN', None))
        repo = github_api.get_repo(
            "%s/%s" % (org, repo)
        )

    if repo is None or not isinstance(repo, Repository):
        raise TypeError("repo expected Repository")

    # Ensure repository matches expression
    if "*" in origin:
        uri = urlparse(origin)
        github_org = uri.path.split('/')[1]
        github_repo = uri.path.split('/')[2]

        if "*" in github_org:
            raise ValueError("cannot use wildcard in GitHub organisation names")

        regex = fnmatch.translate(github_repo)
        reobj = re.compile(regex)
        match = reobj.match(repo.name)

        if match is None:
            return

    _type, _name, _, _ = break_component_naming_format(repo.name)

    item = ManifestItem(
        provider=ListProviderType.GITHUB,
        name=_name,
        description=repo.description,
        type=_type.shortname,
        dist=UNIKRAFT_RELEASE_STABLE,
        git=repo.git_url,
        manifest=origin,
    )

    for branch in repo.get_branches():
        if branch.name == UNIKRAFT_RELEASE_STABLE:
            dist = ManifestItemDistribution(
                name=UNIKRAFT_RELEASE_STABLE
            )

            tags = repo.get_tags()
            releases = repo.get_releases()
            did_add_version = False
            if releases.totalCount > 0:
                for release in releases:
                    # Skip draft releases
                    if release.draft:
                        continue

                    _version = release.tag_name

                    # interpret the tag name for symbolic distributions
                    ref = GIT_UNIKRAFT_TAG_PATTERN.match(release.tag_name)
                    if ref is not None:
                        _version = ref.group(1)

                    did_add_version = True
                    dist.add_version(ManifestItemVersion(
                        git_sha=release.tag_name,
                        version=_version,
                        timestamp=release.published_at,
                        tarball=GITHUB_TARBALL % (
                            repo.owner.login,
                            repo.name,
                            release.tag_name
                        ),
                    ))

            if tags.totalCount > 0:
                for tag in tags:
                    _version = tag.name

                    # interpret the tag name for symbolic distributions
                    ref = GIT_UNIKRAFT_TAG_PATTERN.match(tag.name)
                    if ref is not None:
                        _version = ref.group(1)

                    did_add_version = True
                    dist.add_version(ManifestItemVersion(
                        git_sha=tag.name,
                        version=_version,
                        timestamp=repo.pushed_at,
                        tarball=GITHUB_TARBALL % (
                            repo.owner.login,
                            repo.name,
                            tag.name
                        ),
                    ))

            if did_add_version is False:
                dist.add_version(ManifestItemVersion(
                    git_sha=branch.commit.sha,
                    version=branch.commit.sha[:7],
                    timestamp=repo.pushed_at,
                    tarball=GITHUB_TARBALL % (
                        repo.owner.login,
                        repo.name,
                        branch.commit.sha
                    ),
                ))

        else:
            dist = ManifestItemDistribution(
                name=branch.name,
            )

            dist.add_version(ManifestItemVersion(
                git_sha=branch.commit.sha,
                version=branch.commit.sha[:7],
                timestamp=repo.pushed_at,
                tarball=GITHUB_TARBALL % (
                    repo.owner.login,
                    repo.name,
                    branch.commit.sha
                ),
            ))

        item.add_distribution(dist)

    return item
