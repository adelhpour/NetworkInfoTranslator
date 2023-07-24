from exports.export_base import NetworkInfoExportBase
import json
from pathlib import Path as pathlib


class NetworkInfoExportToEscher(NetworkInfoExportBase):
    def __init__(self):
        self.nodes = {}
        super().__init__()

    def reset(self):
        super().reset()
        self.nodes = {}
        self.reactions = {}

    def add_species(self, species):
        if 'id' in list(species.keys()) and 'referenceId' in list(species.keys()):
            node = self.create_node_from_species(species)
            self.nodes.update(node)

    def add_reaction(self, reaction):
        if 'id' in list(reaction.keys()) and 'referenceId' in list(reaction.keys()):
            self.nodes.update(self.create_node_from_reaction(reaction))
            self.reactions.update(self.create_escher_reaction(reaction))

            if 'speciesReferences' in list(reaction.keys()):
                for species_reference in reaction['speciesReferences']:
                    self.add_species_reference(reaction, species_reference)

    def add_species_reference(self, reaction, species_reference):
        if 'id' in list(species_reference.keys()) and 'referenceId' in list(species_reference.keys()) \
                and 'species' in list(species_reference.keys()) and 'features' in list(species_reference.keys()):
            sr_index = len(species_reference['features']['curve']) - 1
            while sr_index > 0:
                self.nodes.update(self.create_node_from_species_reference(reaction, species_reference, sr_index))
                sr_index = sr_index - 1

    def create_node_from_species(self, species):
        node = self.initialize_item(species)
        self.set_item_biggid(node, species)
        self.set_node_is_primary(node, species)
        self.extract_node_features(node, species)
        node[species['id']]['type'] = "metabolite"
        return node

    def create_node_from_reaction(self, reaction):
        node = self.initialize_item(reaction)
        self.set_item_biggid(node, reaction)
        self.set_node_is_primary(node, reaction)
        self.extract_node_features(node, reaction)
        node[reaction['id']]['type'] = "midmarker"
        return node

    def create_node_from_species_reference(self, reaction, species_reference, sr_index):
        return self.initialize_species_reference_node(reaction, species_reference, sr_index)

    def create_escher_reaction(self, reaction):
        escher_recaction = self.initialize_item(reaction)
        self.set_item_biggid(escher_recaction, reaction)
        self.extract_escher_reaction_features(escher_recaction, reaction)
        return escher_recaction

    @staticmethod
    def initialize_item(go):
        return {go['id']: {}}

    @staticmethod
    def initialize_species_reference_node(reaction, species_reference, sr_index):
        species_reference_node_features = {'type': "multimarker"}
        species_reference_node_features['x'] = 0.5 * (species_reference['features']['curve'][sr_index]['startX'] +
                                                      species_reference['features']['curve'][sr_index - 1]['endX'])
        species_reference_node_features['y'] = 0.5 * (species_reference['features']['curve'][sr_index]['startY'] +
                                                      species_reference['features']['curve'][sr_index - 1]['endY'])
        return {reaction['id'] + "." + species_reference['id'] + ".M" + str(sr_index + 1):
                    species_reference_node_features}

    @staticmethod
    def set_item_biggid(item, go):
        if 'referenceId' in list(go.keys()):
            item[go['id']]['bigg_id'] = go['referenceId']

    @staticmethod
    def set_node_is_primary(node, go):
        node[go['id']]['node_is_primary'] = True

    def extract_node_features(self, node, go):
        if 'features' in list(go.keys()):
            node[go['id']]['x'], node[go['id']]['y'] = self.get_position(go['features'])

            if 'texts' in list(go.keys()):
                for text in go['texts']:
                    if 'features' in list(text.keys()):
                        node[go['id']]['name'] = self.get_name(text['features'])
                        node[go['id']]['label_x'], node[go['id']]['label_y'] = self.get_position(text['features'])


    def extract_escher_reaction_features(self, escher_recaction, reaction):
        escher_recaction[reaction['id']]['reversibility'] = self.get_reaction_reversibility(reaction)
        if 'features' in list(reaction.keys()):
            escher_recaction[reaction['id']]['label_x'], escher_recaction[reaction['id']]['label_y'] =\
                self.get_position(reaction['features'])

        if 'speciesReferences' in list(reaction.keys()):
            segments = []
            metabolites = []
            for species_reference in reaction['speciesReferences']:
                if 'role' in list(species_reference.keys()):
                    if species_reference['role'].lower() == "product":
                        metabolites.append(self.create_metabolite_from_product(species_reference))
                    if species_reference['role'].lower() == "reactant" or species_reference['role'].lower() == "substrate":
                        metabolites.append(self.create_metabolite_from_substrate(species_reference))
            escher_recaction[reaction['id']]['segments'] = segments
            escher_recaction[reaction['id']]['metabolites'] = metabolites

    def get_reaction_reversibility(self, reaction):
        if reaction['SBMLObject']:
            return reaction['SBMLObject'].getReversible()
        return False

    def create_metabolite_from_product(self, species_reference):
        coefficient = 1
        if species_reference['SBMLObject']:
            coefficient = species_reference['SBMLObject'].getStoichiometry()
        return {'bigg_id': species_reference['species'], 'coefficient': coefficient}

    def create_metabolite_from_substrate(self, species_reference):
        coefficient = -1
        if species_reference['SBMLObject']:
            coefficient = -1 * species_reference['SBMLObject'].getStoichiometry()
        return {'bigg_id': species_reference['species'], 'coefficient': coefficient}

    def get_position(self, features):
        if 'boundingBox' in list(features.keys()):
            return self.get_bb_center_x(features['boundingBox']), self.get_bb_center_y(features['boundingBox'])
        elif 'curve' in list(go['features'].keys()):
            return self.get_curve_center_x(features['curve']), self.get_curve_center_y(features['curve'])
        return 0.0, 0.0

    @staticmethod
    def get_bb_center_x(bounding_box):
        return bounding_box['x'] + 0.5 * bounding_box['width']

    @staticmethod
    def get_bb_center_y(bounding_box):
        return bounding_box['y'] + 0.5 * bounding_box['height']

    @staticmethod
    def get_curve_center_x(curve):
        if len(curve):
            return 0.5 * (curve[0]['startX'] + curve[len(curve) - 1]['endX'])
        return 0.0

    @staticmethod
    def get_curve_center_y(curve):
        if len(curve):
            return 0.5 * (curve[0]['startY'] + curve[len(curve) - 1]['endY'])
        return 0.0

    @staticmethod
    def get_name(features):
        if 'plainText' in list(features.keys()):
            return features['plainText']
        return ""

    def export(self, file_name="file"):
        position_x = self.graph_info.extents['minX'] + 0.5 * (self.graph_info.extents['maxX'] - self.graph_info.extents['minX'])
        position_y = self.graph_info.extents['minY'] + 0.5 * (self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])
        dimensions_width = self.graph_info.extents['maxY'] - self.graph_info.extents['minY']
        dimensions_height = self.graph_info.extents['maxY'] - self.graph_info.extents['minY']
        graph_info = [{'generated_by': "SBMLplot",
                      'name': pathlib(file_name).stem + "_graph",
                      'canvas': {'x': position_x, 'y': position_y, 'width': dimensions_width, 'height': dimensions_height},
                      'nodes': self.nodes,
                      'reactions': self.reactions}]
        with open(file_name.split('.')[0] + ".json", 'w', encoding='utf8') as js_file:
            json.dump(graph_info, js_file, indent=1)
        return graph_info