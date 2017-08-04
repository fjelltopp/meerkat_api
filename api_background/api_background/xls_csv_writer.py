import csv
import os

import xlsxwriter


class XlsCsvFileWriter:
    def __init__(self, base_directory, form_name, directory_name):
        self.form_name = form_name
        self.directory_name = directory_name

        self.csv_row_index = 0
        self.xls_row_index = 0
        self.csv_writer_row_buffer = []
        self.csv_content = None
        self.csv_writer = None
        self.xls_sheet = None
        self.xls_book = None
        self.xls_content = None

        self.__initialize(base_directory)

    def __initialize(self, base_directory):
        self.file_directory = base_directory + "/exported_data/" + self.directory_name + "/"
        self.file_path_template = self.file_directory + self.form_name + ".{}"
        os.mkdir(self.file_directory)

        self.__create_csv_file()
        self.__create_xls_file()

    def __create_csv_file(self):
        file_path = self.file_path_template.format("csv")
        self.csv_content = open(file_path, "w")
        self.csv_writer = csv.writer(self.csv_content)

    def __create_xls_file(self):
        file_path = self.file_path_template.format("xlsx")
        self.xls_content = open(file_path, "wb")
        # XlsxWriter with "constant_memory" set to true, flushes mem after each row
        self.xls_book = xlsxwriter.Workbook(self.xls_content, {'constant_memory': True})
        self.xls_sheet = self.xls_book.add_worksheet()

    def close_cvs_xls_buffers(self):
        self.flush_csv_buffer()
        self.csv_content.close()

        self.xls_book.close()
        self.xls_content.close()

    def write_xls_row(self, data):
        # Little utility function write a row to file.
        for cell in range(len(data)):
            self.xls_sheet.write(self.xls_row_index, cell, data[cell])
        self.xls_row_index += 1

    def write_csv_row(self, row):
        self.csv_writer_row_buffer.append(row)
        if self.csv_row_index % 5 == 0:
            self.flush_csv_buffer()
        self.csv_row_index += 1

    def flush_csv_buffer(self):
        self.csv_writer.writerows(self.csv_writer_row_buffer)
        self.csv_writer_row_buffer = []
