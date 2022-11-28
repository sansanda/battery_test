'''
Created on 15 jul. 2019

@author: mespower
'''

#CSV file

import csv
from csv import Error

        
def create_csv_file(_csv_path,_field_names):
    '''
    This function creates the csv file. If an error occur, it will be printed.
    '''

    try:
        #Configure the file by setting the delimiters, lineterminators...
        csv.register_dialect('myDialect',delimiter = ',',quoting=csv.QUOTE_NONE,lineterminator = '\n',escapechar=' ', quotechar=' ',skipinitialspace=True)
        f = open(_csv_path, 'w')    #Open the file as writers
        writer = csv.DictWriter(f, fieldnames=_field_names)
        writer.writeheader()
        f.close()
 
    except Error:
        print(Error)
             

def insertRowInCSV(_csv_path,_rowValues):
    '''
    This function adds lines into the file
    '''
    f = open(_csv_path, 'a')    #Open the file in append mode, in order to not substitute the existing info
    with f:
        writer = csv.writer(f, dialect='myDialect')
        writer.writerow(_rowValues)    #_rowValues will be the info added to the file 
    f.close()

  

