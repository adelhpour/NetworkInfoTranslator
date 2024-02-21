import networkinfotranslator

file_path = "path/to/.xml/file"
output_file_directory = "/path/to/output/directory"
sbml_import = networkinfotranslator.NetworkInfoImportFromSBMLModel()
sbml_import.extract_info(file_path)
skia_export = networkinfotranslator.NetworkInfoExportToSkia()
skia_export.extract_graph_info(sbml_import)
skia_export.export(file_directory=output_file_directory, file_name="network", file_format="png")
