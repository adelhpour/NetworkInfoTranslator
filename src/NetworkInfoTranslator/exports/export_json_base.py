from .export_base import NetworkInfoExportBase


class NetworkInfoExportToJsonBase(NetworkInfoExportBase):
    def __init__(self):
        self.nodes = []
        self.edges = []
        super().__init__()

    def reset(self):
        super().reset()
        self.nodes.clear()
        self.edges.clear()

    def add_compartment(self, compartment):
        if 'id' in list(compartment.keys()) and 'referenceId' in list(compartment.keys()):
            self.add_node(compartment, "Compartment")

    def add_species(self, species):
        if 'id' in list(species.keys()) and 'referenceId' in list(species.keys()):
            self.add_node(species, "Species")

    def add_reaction(self, reaction):
        if 'id' in list(reaction.keys()) and 'referenceId' in list(reaction.keys()):
            self.add_node(reaction, "Reaction")

            if 'speciesReferences' in list(reaction.keys()):
                for sr in reaction['speciesReferences']:
                    self.add_species_reference(reaction, sr)

    def add_species_reference(self, reaction, species_reference):
        if 'id' in list(species_reference.keys()) and 'referenceId' in list(species_reference.keys()) \
                and 'species' in list(species_reference.keys()):
            self.add_edge(species_reference, reaction)

    def add_node(self, go):
        pass

    def add_edge(self, species_reference, reaction):
        pass