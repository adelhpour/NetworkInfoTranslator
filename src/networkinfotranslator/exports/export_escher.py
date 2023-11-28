import libsbmlnetworkeditor
from .export_base import NetworkInfoExportBase
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
                and 'species' in list(species_reference.keys()) and 'features' in list(species_reference.keys())\
                and 'curve' in list(species_reference['features'].keys()):
            sr_index = len(species_reference['features']['curve']) - 1
            while sr_index > 0:
                self.nodes.update(self.create_node_from_species_reference(reaction, species_reference, sr_index))
                sr_index = sr_index - 1

    def create_node_from_species(self, species):
        node = self.initialize_item(species)
        self.set_item_biggid(node, species)
        self.set_node_is_primary(node, species)
        self.extract_node_features(node, species)
        node[species['id']]['node_type'] = "metabolite"
        return node

    def create_node_from_reaction(self, reaction):
        node = self.initialize_item(reaction)
        self.set_item_biggid(node, reaction)
        self.set_node_is_primary(node, reaction)
        self.extract_node_features(node, reaction)
        node[reaction['id']]['node_type'] = "midmarker"
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
                        horizontal_padding = 20
                        vertical_padding = -20
                        node[go['id']]['label_x'] += horizontal_padding
                        node[go['id']]['label_y'] += vertical_padding


    def extract_escher_reaction_features(self, escher_recaction, reaction):
        escher_recaction[reaction['id']]['reversibility'] = self.get_reaction_reversibility(reaction)
        if 'features' in list(reaction.keys()):
            escher_recaction[reaction['id']]['name'] = escher_recaction[reaction['id']]['bigg_id']
            escher_recaction[reaction['id']]['label_x'], escher_recaction[reaction['id']]['label_y'] =\
                self.get_position(reaction['features'])
            horizontal_padding = 0
            vertical_padding = -20
            escher_recaction[reaction['id']]['label_x'] += horizontal_padding
            escher_recaction[reaction['id']]['label_y'] += vertical_padding


        if 'speciesReferences' in list(reaction.keys()):
            segments = {}
            metabolites = []
            for species_reference in reaction['speciesReferences']:
                if 'role' in list(species_reference.keys()):
                    if species_reference['role'].lower() == "product":
                        metabolites.append(self.create_metabolite_from_product(species_reference))
                    elif species_reference['role'].lower() == "reactant" or species_reference['role'].lower() == "substrate":
                        metabolites.append(self.create_metabolite_from_substrate(species_reference))
                segments.update(self.create_segments(species_reference, reaction))
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

    def create_segments(self, species_reference, reaction):
        segments = {}
        segment_id = species_reference['id'] + ".S" + "0"
        segment_features = {}
        if 'curve' in list(species_reference['features'].keys()):
            segment_features['from_node_id'] = reaction['id']
            for cs_index in range(libsbmlnetworkeditor.getNumCurveSegments(species_reference['glyphObject']) - 1):
                segment_features['to_node_id'] = reaction['id'] + "." + species_reference['id'] + ".M" + str(cs_index + 1)
                segment_features.update(self.get_segment_base_point_features(species_reference['features']['curve'], cs_index))
                segments.update({segment_id: segment_features})
                segment_id = species_reference['id'] + ".S" + str(cs_index + 1)
                segment_features['from_node_id'] = reaction['id'] + "." + species_reference['id'] + ".M" + str(cs_index + 1)
            segment_features.update(self.get_segment_base_point_features(species_reference['features']['curve'], -1))
            segment_features['to_node_id'] = libsbmlnetworkeditor.getSpeciesGlyphId(species_reference['glyphObject'])
        segments.update({segment_id: segment_features})
        return segments

    def get_position(self, features):
        if 'boundingBox' in list(features.keys()):
            return self.get_bb_center_x(features['boundingBox']), self.get_bb_center_y(features['boundingBox'])
        elif 'curve' in list(go['features'].keys()):
            return [self.get_curve_center_x(features['curve']), self.get_curve_center_y(features['curve'])]
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

    @staticmethod
    def get_segment_base_point_features(curve, cs_index):
        if 'basePoint1X' in list(curve[cs_index].keys()) and 'basePoint2X' in list(curve[cs_index].keys()):
            return {'b1': {'x': curve[cs_index]['basePoint1X'], 'y': curve[cs_index]['basePoint1Y']},
                    'b2': {'x': curve[cs_index]['basePoint2X'], 'y': curve[cs_index]['basePoint2Y']}}
        else:
            return {'b1': {'x': curve[cs_index]['startX'], 'y': curve[cs_index]['startY']},
                    'b2': {'x': curve[cs_index]['endX'], 'y': curve[cs_index]['endY']}}

    def export(self, file_name="file"):
        horizontal_margin = 75
        vertical_margin = 75
        position_x = self.graph_info.extents['minX'] - horizontal_margin
        position_y = self.graph_info.extents['minY'] - vertical_margin
        dimensions_width = self.graph_info.extents['maxX'] - self.graph_info.extents['minX'] + 2 * horizontal_margin
        dimensions_height = self.graph_info.extents['maxY'] - self.graph_info.extents['minY'] + 2 * vertical_margin
        graph_info = [{'map_name': pathlib(file_name).stem + "_graph",
                       'map_id': "",
                       'map_description': "",
                       'homepage': ""},
                      {'canvas': {'x': position_x, 'y': position_y, 'width': dimensions_width, 'height': dimensions_height},
                      'nodes': self.nodes,
                      'reactions': self.reactions}]
        with open(file_name.split('.')[0] + ".json", 'w', encoding='utf8') as js_file:
            json.dump(graph_info, js_file, indent=1)
        return graph_info