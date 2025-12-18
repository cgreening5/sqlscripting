from typing import override
import unittest

from node import Builder
from scripter import InsertScripter
from dataservice import DataService

_schema = {
    "dbo": {
        "Applications": {
            "columns": ["id"],
            "rows": {
                1: {"id": 1},
            },
            "foreign_keys": []
        },
        "ApplicationProgramIntakes": {
            "columns": ["id", "application_id"],
            "foreign_keys": [
                ("dbo", "Applications", "id", "application_id", "FK_ApplicationProgramIntakes_Applications")
            ],
            "rows": {
                5: {"id": 5, "application_id": 1},
            }
        }
    },
    "admin": {
        "ApplicationVetting": {
            "columns": ["id", "application_id"],
            "foreign_keys": [("dbo", "Applications", "id", "application_id", "FK_ApplicationVetting_Applications")],
            "rows": {
                10: {"id": 10, "application_id": 1},
            }
        },
        "program_vetting": {
            "columns": ["id", "application_vetting_id", "application_program_intake_id"],
            "foreign_keys": [
                ("admin", "ApplicationVetting", "id", "application_vetting_id", "FK_ProgramVetting_ApplicationVetting"),
                ("dbo", "ApplicationProgramIntakes", "id", "application_program_intake_id", "FK_ProgramVetting_ApplicationProgramIntakes"),
            ],
            "rows": {
                100: {"id": 100, "application_vetting_id": 10, "application_program_intake_id": 5},
            }
        }
    }
}

class MockDataService(DataService):

    def __init__(self):
        pass

    @override
    def get_columns(self, schema: str, table_name: str) -> list[str]:
        return _schema[schema][table_name]['columns']
    
    @override
    def get_references(self, schema: str, table_name: str) -> list[tuple[str, str, str, str, str]]:
        return _schema[schema][table_name]['foreign_keys']
    
    @override
    def get_back_references(self, table_name: str) -> list[tuple[str, str, str, str, str]]:
        refs = []
        for ref_schema, tables in _schema.items():
            for ref_table, ref_table_info in tables.items():
                for fk in ref_table_info.get('foreign_keys', []):
                    pk_schema, pk_table, pk_column, fk_column, fk_name = fk
                    if pk_table == table_name:
                        refs.append((pk_column, ref_schema, ref_table, fk_column, fk_name))
        return refs
    
    @override
    def get_values(self, table_name, identity_col, id, columns, schema='dbo'):
         table = _schema[schema][table_name]
         return [table['rows'][id][column] for column in columns]
    
    @override
    def get_identity(self, table_name, schema='dbo'):
        return 'id'
    
    @override
    def get_referencing_rows(self, schema, table_name, fk_name, fk_val):
        table = _schema[schema][table_name]
        _, _, _, fk_column, _ = next(fk for fk in table['foreign_keys'] if fk[4] == fk_name)
        ids = []
        for id, row in table['rows'].items():
            if row[fk_column] == fk_val:
                ids.append(id)
        return ids

class TestNodeBuilder(unittest.TestCase):

    def test_build_diamond_nodes(self):
        dataservice = MockDataService()
        builder = Builder(dataservice, foreign_keys=[])
        node = builder.build_node('dbo', 'Applications', 1)
        print('\n'.join(InsertScripter(node).script()))

    def test_back_references(self):
        dataservice = MockDataService()
        ref = dataservice.get_back_references('Applications')[1]
        assert ref[0] == 'id', f"Expected 'id', got {ref[0]}"
        assert ref[1] == 'admin', f"Expected 'admin', got {ref[1]}"
        assert ref[2] == 'ApplicationVetting', f"Expected 'ApplicationVetting', got {ref[2]}"
        assert ref[3] == 'application_id', f"Expected 'application_id', got {ref[3]}"
        assert ref[4] == 'FK_ApplicationVetting_Applications', f"Expected 'FK_ApplicationVetting_Applications', got {ref[4]}"

if __name__ == '__main__':
    unittest.main()