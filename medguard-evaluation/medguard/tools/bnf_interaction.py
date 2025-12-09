import json
import logging
from pathlib import Path
from typing import List, Optional, Type, Union

import pandas as pd
from inspect_ai.tool import tool
from markdownify import markdownify
from pydantic import AnyUrl, BaseModel
from rapidfuzz import process


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


# Get the project root and construct data paths relative to it
project_root = get_project_root()
data_root = project_root / ".data"

DRUG_INTERACTION_PROFILE_LOC = str(data_root / "bnf-drug-data/data/drug_interaction_slugs.tsv")
DRUG_INTERACTION_SPECIFIC_LOC = str(
    data_root / "bnf-drug-data/data/drug_interactions/{drug_name}.json"
)
BRAND_DRUG_LOC = str(data_root / "bnf-drug-data/data/synonyms.tsv")

DEFAULT_THRESHOLD = 90  # Fuzzy matching threshold


class Interaction(BaseModel):
    """BNF drug interactions"""

    # TODO these should be constrained to only allow the expected values
    root_drug: str
    drug_name: str
    severity: str
    additiveEffect: bool
    description: str
    url: Optional[Union[AnyUrl, str]] = None  # allow string so it is JSON serializable
    evidence: Optional[Union[str, Type[None]]] = None

    @property
    def prompt(self) -> str:
        tmp_prompt = ""
        tmp_prompt += f"#### {self.root_drug} -- {self.drug_name}\n\r"
        tmp_prompt += f"Severity: {self.severity}\n\r"
        tmp_prompt += f"Additive Effects: {self.additiveEffect}\n\r"
        tmp_prompt += f"Evidence for Interaction: {self.evidence}\n\r"
        tmp_prompt += f"Description: {markdownify(self.description)}\n\r"
        tmp_prompt += "----\n"
        return tmp_prompt


class InteractionList(BaseModel):
    """List of BNF drug interactions"""

    interactions: List[Interaction] = []
    no_match: Optional[List] = []

    @property
    def prompt(self) -> str:
        if len(self.interactions) == 0:
            return "No interactions were found between the given drugs."

        prompt = "The following interactions were found:\n====\n"
        for interaction in self.interactions:
            prompt += interaction.prompt
        # TODO the below is not formatted correctly so commented out
        if self.no_match:
            prompt += "\n\n Some drugs were not found in the BNF database and therefore could not be checked for interactions:"
            # for item in self.no_match:
            #    tmp_prompt += f"\n{item[0]}"
        return prompt


def map_ingredients(
    drug_name: str, synonyms: dict, threshold: int = DEFAULT_THRESHOLD
) -> list[str]:
    """Resolve a drug name to a list of ingredients"""
    drug_name = drug_name.lower().strip()  # standardize to lower case

    if drug_name in synonyms:
        # First check for a fast direct match
        return synonyms[drug_name].split(", ")
    else:
        # Else find the best match among all brand names
        best_match = process.extractOne(drug_name, synonyms.keys())
        if best_match[1] > threshold:
            return synonyms[best_match[0]].split(", ")
        else:
            logging.info(f"Could not find a synonym match for {drug_name}")
            return drug_name


def ingredient_to_bnf_interactions(
    ingredient: str, bnf_interactions: dict, threshold: int = DEFAULT_THRESHOLD
) -> str:
    """Resolve a single ingredient to a BNF profile slug"""
    ingredient = ingredient.lower().strip()  # standardize to lower case

    if ingredient in bnf_interactions:
        # First check for a fast direct match
        return bnf_interactions[ingredient]
    else:
        # Else find the best match among all brand names
        best_match = process.extractOne(ingredient, bnf_interactions.keys())
        if best_match[1] > threshold:
            return bnf_interactions[best_match[0]]
        else:
            raise ValueError(f"Could not find a BNF interaction slug match for {ingredient}")


def ingredients_to_bnf_interactions(
    ingredients: list, bnf_interactions: dict, threshold: int = DEFAULT_THRESHOLD
) -> list[str]:
    """Resolve a list of ingredients to a BNF profile slug"""
    interaction_slugs = []
    for i in ingredients:
        try:
            interaction_slugs.append(ingredient_to_bnf_interactions(i, bnf_interactions, threshold))
        except ValueError:
            continue
    return interaction_slugs


def resolve_drug_interactions(
    drug_name: str,
    synonyms: dict,
    bnf_interactions: dict,
    threshold: int = DEFAULT_THRESHOLD,
) -> list[str]:
    """Resolve a drug name to a list of BNF interactions slugs"""

    drug_name = drug_name.lower().strip()  # standardize to lower case

    # first try a direct match
    if drug_name in bnf_interactions:
        return [bnf_interactions[drug_name]]
    else:
        # get the ingredients for the drug
        drug_ingredients = map_ingredients(drug_name, synonyms, threshold)

        if isinstance(drug_ingredients, str):
            ingredients = drug_ingredients.split(", ")
        elif isinstance(drug_ingredients, list):
            ingredients = drug_ingredients
        else:
            raise ValueError("Unexpected type for drug_ingredients")

        # get the interactions slug for each ingredient
        slugs = []
        for ingredient in ingredients:
            try:
                if len(ingredients) == 1:
                    slug = ingredient_to_bnf_interactions(ingredient, bnf_interactions, threshold)
                else:
                    slug = ingredients_to_bnf_interactions(
                        [ingredient], bnf_interactions, threshold
                    )
                slugs.extend(slug if isinstance(slug, list) else [slug])
            except ValueError:
                continue

        return slugs


def format_interactions(drug_a: str, profile: dict) -> List[dict]:
    interactions = []
    for interaction in profile["result"]["data"]["bnfInteractant"]["interactions"]:
        # To make subsequent comparison easier, sort the drugs by name
        drug_b = interaction["interactant"]["title"]
        interactions.append(
            {
                "drug_a": drug_a,
                "drug_b": drug_b,
                "severity": interaction["messages"][0]["severity"],
                "additiveEffect": interaction["messages"][0]["additiveEffect"],
                "evidence": interaction["messages"][0]["evidence"],
                "description": interaction["messages"][0]["message"],
            }
        )
    return interactions


def de_duplicate_interactions(interactions: List[dict]) -> List[dict]:
    """De-duplicate a list of interaction dictionaries based on drug_a and drug_b."""
    unique_interactions = []
    seen_pairs = set()
    for interaction in interactions:
        # Ensure order doesn't matter for the pair by sorting
        pair = tuple(sorted((interaction["drug_a"], interaction["drug_b"])))
        if pair not in seen_pairs:
            unique_interactions.append(interaction)
            seen_pairs.add(pair)
    return unique_interactions


@tool
def get_bnf_drug_interactions(
    drug_interaction_list: str = DRUG_INTERACTION_PROFILE_LOC,
    drug_interaction_loc: str = DRUG_INTERACTION_SPECIFIC_LOC,
    brand_lookup: str = BRAND_DRUG_LOC,
    threshold: int = DEFAULT_THRESHOLD,
):
    synonyms = pd.read_csv(brand_lookup, index_col=0, sep="\t")["bnf_name"].to_dict()
    bnf_interactions = pd.read_csv(drug_interaction_list, index_col=0, sep="\t")["slug"].to_dict()

    async def execute(drug_list: list[str]) -> str:
        """
        This function will return the drug interaction information for the given list of drugs through querying the British National Formulary (BNF) database.

        Example: [aspirin, paracetamol, warfarin, tagrisso] to check interactions between these drugs.

        Args:
            drug_list (list[str]): The name of the drug/s to look up. Use single brand or chemical name for the drug and no extra information such as quantity. E.g ['Tagrisso', 'Co-codamol', 'Paracetamol'].

        Returns:
            The drug-drug interaction information for the given drugs.
        """

        try:
            # Convert all drug names to lowercase for case-insensitive matching
            drug_list = [drug_name.lower().capitalize() for drug_name in drug_list]

            # Resolve the user provided drug names to a list of BNF interaction slugs
            # These are either the drug name, matches to the BNF interaction slug, or a list of slugs for the underlying ingredients
            drug_interactions = {}
            for drug_name in drug_list:
                if drug_name in drug_interactions:
                    continue  # skip if already resolved
                else:
                    drug_interactions[drug_name] = resolve_drug_interactions(
                        drug_name, synonyms, bnf_interactions, threshold
                    )

            # Now we have the list of BNF interaction slugs, we can load the interactions from the BNF interaction database
            interactions = []
            for drug_name, drug_slugs in drug_interactions.items():
                # get the interactions for each ingredient
                for drug_slug in drug_slugs:
                    try:
                        with open(drug_interaction_loc.format(drug_name=drug_slug)) as file:
                            profile = json.load(file)

                        interactions.extend(format_interactions(drug_name, profile))
                    except FileNotFoundError:
                        logging.exception(f"Could not find interactions file for {drug_slug}")

            # De-duplicate the interactions, and then ensure we're only looking at interactions between the drugs in the original drug list
            interactions = de_duplicate_interactions(interactions)

            # check for flagged interactions
            flagged_interactions = InteractionList()
            for interaction in interactions:
                if interaction["drug_a"] in drug_list and interaction["drug_b"] in drug_list:
                    flagged_interactions.interactions.append(
                        Interaction(
                            root_drug=interaction["drug_a"],
                            drug_name=interaction["drug_b"],
                            severity=interaction["severity"],
                            additiveEffect=interaction["additiveEffect"],
                            evidence=interaction["evidence"],
                            description=interaction["description"],
                            url=None,
                        )
                    )
            return flagged_interactions.prompt

        except ValueError:
            return f"Could not find a BNF interaction slug match for {drug_list}, please continue with the next drug."

    return execute
