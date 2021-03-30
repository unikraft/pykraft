#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Alexander Jung <alexander.jung@neclab.eu>
#
# Copyright (c) 2020, NEC Laboratories Europe GmbH.,
#                     NEC Corporation. All rights reserved.
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

# Influential environmental variables
WORKDIR=${WORKDIR:-$(pwd)/.concourse}
TMPLDIR=${TMPLDIR:-$WORKDIR/templates}
OUTDIR=${OUTDIR:-$WORKDIR/pipelines}
BRANCH=${BRANCH:-staging}

_help() {
    cat <<EOF
$0 - Generate kraft-centric pipelines for Concourse.

The default operation with no arguments is to generate all possible
pipelines available.

Usage:
  $0 [OPTIONS]

Options:
  -s --self     Generate reconfiguration pipeline only.
  -h --help     Show this help menu and exit.
     --pr       Only generate Pull Request pipelines.
     --staging  Only generate staging pipelines.
     --stable   Only generate stable pipelines.

Influential environmental variables:
  TMPLDIR       The directory where the templates reside
                  (default $TMPLDIR).
  OUTDIR        The output directory for the pipelines
                  (default $OUTDIR).

Help:
  For help using this tool, please refer to the README.md at
  https://github.com/unikraft/kraft.git
EOF
}

TEMPLATE_NOTICE="# This file was auto-generated on `date`."

GENERATE_PR=y
GENERATE_STAGING=y
GENERATE_STABLE=y
GENERATE_SELF=y
GENERATE_KRAFT=y
SHOW_HELP=n

# Parse arguments
for i in "$@"; do
  case $i in
    --pr)
      GENERATE_STAGING=n
      GENERATE_STABLE=n
      ;;
    --staging)
      GENERATE_PR=n
      GENERATE_STABLE=n
      ;;
    --stable)
      GENERATE_PR=n
      GENERATE_STAGING=n
      ;;
    -s|--self)
      GENERATE_KRAFT=n
      ;;
    -h|--help)
      SHOW_HELP=y
      ;;
    *)
      ;;
  esac
done

if [[ $SHOW_HELP == 'y' ]]; then
  _help
  exit 0
fi

if [[ $GENERATE_PR == 'y' ]]; then
  echo "Generating pull-request pipeline..."

  KRAFTTEMPDIR_PR=$(mktemp -d)
  cat $TMPLDIR/pr.yml > $KRAFTTEMPDIR_PR/template.yml
  cat $TMPLDIR/data.yml > $KRAFTTEMPDIR_PR/data.yml
  echo $TEMPLATE_NOTICE > $OUTDIR/kraft-pr.yml

  echo " ... saving $OUTDIR/kraft-pr.yml"
  ytt \
    --data-value branch=$BRANCH \
    --file $TMPLDIR/mixins.lib.yml \
    --file $KRAFTTEMPDIR_PR \
      >> $OUTDIR/kraft-pr.yml
fi

if [[ $GENERATE_STAGING == 'y' ]]; then
  echo "Generating staging pipeline..."

  KRAFTTEMPDIR_STAGING=$(mktemp -d)
  cat $TMPLDIR/staging.yml > $KRAFTTEMPDIR_STAGING/template.yml
  cat $TMPLDIR/data.yml > $KRAFTTEMPDIR_STAGING/data.yml
  echo $TEMPLATE_NOTICE > $OUTDIR/kraft-staging.yml

  echo " ... saving $OUTDIR/kraft-staging.yml"
  ytt \
    --data-value branch=$BRANCH \
    --file $TMPLDIR/mixins.lib.yml \
    --file $KRAFTTEMPDIR_STAGING \
      >> $OUTDIR/kraft-staging.yml
fi

if [[ $GENERATE_STABLE == 'y' ]]; then
  echo "Generating stable pipeline..."

  KRAFTTEMPDIR_STABLE=$(mktemp -d)
  cat $TMPLDIR/stable.yml > $KRAFTTEMPDIR_STABLE/template.yml
  cat $TMPLDIR/data.yml > $KRAFTTEMPDIR_STABLE/data.yml
  echo $TEMPLATE_NOTICE > $OUTDIR/kraft-stable.yml

  echo " ... saving $OUTDIR/kraft-stable.yml"
  ytt \
    --data-value branch=$BRANCH \
    --file $TMPLDIR/mixins.lib.yml \
    --file $KRAFTTEMPDIR_STABLE \
      >> $OUTDIR/kraft-stable.yml
fi

# if [[ $GENERATE_SELF == '' ]]; then

# fi
