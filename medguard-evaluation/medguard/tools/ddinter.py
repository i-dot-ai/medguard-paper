import os

import pandas as pd
from inspect_ai.tool import tool
from pydantic import BaseModel
from rapidfuzz import process


class Interaction(BaseModel):
    source_drug: str
    target_drug: str
    interaction_level: str
    interaction_type: str

    @property
    def prompt(self) -> str:
        return f"Drug Interaction: {self.source_drug} - {self.target_drug} | Interaction Level: {self.interaction_level} | Interaction Type: {self.interaction_type}"


class DDInterLoader:
    def __init__(self, input_path: str = ".data/ddinter2"):
        self.dataset_to_content_map = {
            "A": "alimentary tract and metabolism",
            "B": "blood and blood forming organs",
            "D": "dermatologicals",
            "H": "systemic hormonal preparations, excluding sex hormones and insulins",
            "L": "antineoplastic and immunomodulating agents",
            "P": "antiparasitic products, insecticides and repellents",
            "R": "respiratory system",
            "V": "various",
        }

        self.input_path = input_path
        self.data = self._load_data(self.dataset_to_content_map)
        self.drug_names = self._load_drug_names(self.data)
        self.matching_threshold = 80

    def _load_data(self, dataset_to_content_map: dict):
        csv_filenames = os.listdir(self.input_path)
        csv_filenames = [f for f in csv_filenames if f.endswith(".csv")]

        csv_filenames = [os.path.join(self.input_path, f) for f in csv_filenames]

        dfs = []
        for filename in csv_filenames:
            df = pd.read_csv(filename)
            lookup_value = filename[-5]
            content = dataset_to_content_map[lookup_value]
            df["interaction_type"] = content
            dfs.append(df)

        columns = {
            "Drug_A": "drug_a",
            "Drug_B": "drug_b",
            "Level": "level",
            "interaction_type": "interaction_type",
        }
        df = pd.concat(dfs).rename(columns=columns)[columns.values()]

        df = (
            pd.concat([df, df.rename(columns={"drug_a": "drug_b", "drug_b": "drug_a"})])
            .drop_duplicates()
            .sort_values(by=["drug_a", "drug_b"])
        )
        return df

    def _load_drug_names(self, data: pd.DataFrame, drug_columns: list[str] = ["drug_a", "drug_b"]):
        drug_names = set(data["drug_a"].to_list() + data["drug_b"].to_list())
        return drug_names

    def _get_closest_drug_name(self, drug_name, drug_names: list[str]) -> str:
        if drug_name in drug_names:
            return drug_name
        else:
            (drug_name, edit_distance, _) = process.extractOne(drug_name, drug_names)
            if edit_distance < self.matching_threshold:
                return None
            else:
                return drug_name

    def _get_drug_pairs(self, drug_names: list[str]) -> list[tuple[str, str]]:
        return [
            (drug_names[i], drug_names[j])
            for i in range(len(drug_names))
            for j in range(i + 1, len(drug_names))
        ]

    def _get_drug_interactions(self, drug_names: list[str]):
        drug_names = [
            self._get_closest_drug_name(drug_name, self.drug_names) for drug_name in drug_names
        ]
        drug_names = [drug_name for drug_name in drug_names if drug_name is not None]
        if len(drug_names) <= 1:
            return [], []
        drug_pairs = self._get_drug_pairs(drug_names)

        dfs = []
        for drug_pair in drug_pairs:
            df = self.data[
                (self.data["drug_a"] == drug_pair[0]) & (self.data["drug_b"] == drug_pair[1])
            ]
            dfs.append(df)

        interactions = pd.concat(dfs).drop_duplicates()
        return (
            [
                Interaction(
                    source_drug=row["drug_a"],
                    target_drug=row["drug_b"],
                    interaction_level=row["level"],
                    interaction_type=row["interaction_type"],
                )
                for index, row in interactions.iterrows()
            ],
            drug_names,
        )

    def _get_all_drug_interactions(self, drug_name: str) -> list[Interaction]:
        drug_name = self._get_closest_drug_name(drug_name, self.drug_names)
        interactions = self.data[self.data["drug_a"] == drug_name]
        return [
            Interaction(
                source_drug=row["drug_a"],
                target_drug=row["drug_b"],
                interaction_level=row["level"],
                interaction_type=row["interaction_type"],
            )
            for index, row in interactions.iterrows()
        ]

    def get_drug_interactions_as_prompt(self, drug_names: list[str]) -> str:
        interactions, closest_names = self._get_drug_interactions(drug_names)

        if len(interactions) > 0:
            prompt = ""
            for original_name, closest_name in zip(drug_names, closest_names):
                if original_name.lower() != closest_name.lower():
                    prompt += f"{original_name} - {closest_name}\n"
            if len(prompt) > 0:
                prompt = (
                    "The following drug name mappings were used to find interactions:\n" + prompt
                )

            prompt += "\nThe following interactions were found in the DDInter2 database:\n"
            for interaction in interactions:
                prompt += f"{interaction.source_drug} - {interaction.target_drug} | {interaction.interaction_level} | {interaction.interaction_type}\n"

        else:
            prompt = "No interactions were found in the DDInter2 database."

        return prompt


@tool
def get_ddinter_drug_interactions() -> str:
    loader = DDInterLoader()

    async def execute(drug_names: list[str]) -> str:
        return loader.get_drug_interactions_as_prompt(drug_names)

    return execute
