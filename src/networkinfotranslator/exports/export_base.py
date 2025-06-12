class NetworkInfoExportBase:
    def __init__(self):
        self.graph_info = None
        self.reset()

    def reset(self):
        self.graph_info = None

    def extract_graph_info(self, graph_info):
        self.reset()
        self.graph_info = graph_info

        # update the features of the entities
        graph_info.extract_entity_features()

        # background canvas
        self.set_background(graph_info)

        # compartments
        for c in graph_info.compartments:
            self.add_compartment(c)

        # species
        for s in graph_info.species:
            self.add_species(s)

        # reactions
        for r in graph_info.reactions:
            self.add_reaction(r)

        # independent text glyphs
        for itg in graph_info.independent_text_glyphs:
            self.add_independent_text_glyph(itg)

        # additional graphical objects
        for go in graph_info.additional_graphical_objects:
            self.add_additional_graphical_object(go)

    def set_background(self, graph_info):
        pass

    def add_compartment(self, compartment):
        pass

    def add_species(self, species):
        pass

    def add_reaction(self, reaction):
        pass

    def add_independent_text_glyph(self, independent_text_glyph):
        pass

    def add_additional_graphical_object(self, additional_graphical_object):
        pass

    def export(self, file_name):
        pass