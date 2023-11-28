import matplotlib.colors as mcolors


class NetworkInfoImportBase:
    def __init__(self):
        self.compartments = []
        self.species = []
        self.reactions = []
        self.colors = []
        self.gradients = []
        self.line_endings = []
        self.extents = {}
        self.background_color = ""

    def reset_info(self):
        self.compartments.clear()
        self.species.clear()
        self.reactions.clear()
        self.colors.clear()
        self.gradients.clear()
        self.line_endings.clear()
        self.extents = {'minX': 0, 'maxX': 0, 'minY': 0, 'maxY': 0}
        self.background_color = "white"

    def find_compartment(self, compartment_reference_id):
        for compartment in self.compartments:
            if compartment_reference_id == compartment['referenceId']:
                return compartment

        return None

    def find_species(self, species_reference_id):
        for species in self.species:
            if species_reference_id == species['referenceId']:
                return species

        return None

    def find_reaction(self, reaction_reference_id):
        for reaction in self.reactions:
            if reaction_reference_id == reaction['referenceId']:
                return reaction

        return None

    def find_color(self, color_id):
        for color in self.colors:
            if color_id == color['id']:
                return color

        return None

    def find_color_value(self, color_id, search_among_gradients=False):
        # search among the gradients
        if search_among_gradients:
            for gradient in self.gradients:
                if color_id == gradient['id'] and 'stops' in list(gradient['features'].keys()):
                    stop_colors = []
                    for stop in gradient['features']['stops']:
                        if 'color' in list(stop.keys()):
                            stop_colors.append(mcolors.to_rgb(
                                find_color_value(graph_info,
                                                 stop['color'])))
                    if len(stop_colors):
                        return mcolors.to_hex(np.average(np.array(stop_colors), axis=0).tolist())

        # search among the colors
        for color in self.colors:
            if color_id == color['id'] and \
                    'value' in list(color['features'].keys()):
                return color['features']['value']
        if color_id.startswith("#"):
            return color_id
        else:
            return "#ffffff"

    def find_color_unique_id(self):
        color_id = "color"
        k = 0
        color_found = True
        while color_found:
            color_found = False
            k = k + 1
            for color in self.colors:
                if color_id + str(k) == color['id']:
                    color_found = True
                    break

        return color_id + str(k)

    def find_line_ending(self, line_ending_id):
        for line_ending in self.line_endings:
            if line_ending_id == line_ending['id']:
                return line_ending

        return None

    def extract_info(self, graph):
        self.reset_info()

    def extract_entity_features(self):
        # compartments
        for compartment in self.compartments:
            self.extract_compartment_features(compartment)

        # species
        for species in self.species:
            self.extract_species_features(species)

        # reactions
        for reaction in self.reactions:
            self.extract_reaction_features(reaction)

            # species references
            if 'speciesReferences' in list(reaction.keys()):
                species_references = reaction['speciesReferences']
                for species_reference in species_references:
                    self.extract_species_reference_features(species_reference)

        # line endings
        for line_ending in self.line_endings:
            self.extract_line_ending_features(line_ending)

        # colors
        for color in self.colors:
            self.extract_color_features(color)

        # gradients
        for gradient in self.gradients:
            self.extract_gradient_features(gradient)