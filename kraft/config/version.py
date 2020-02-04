



from distutils.version import LooseVersion

class SpecificationVersion(LooseVersion):
    """ A hashable version object """
    def __hash__(self):
        return hash(self.vstring)
