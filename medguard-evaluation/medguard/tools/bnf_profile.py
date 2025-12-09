import json
import logging
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
from inspect_ai.tool import tool
from markdownify import markdownify
from pydantic import BaseModel, Field
from rapidfuzz import process

# Get the project root and construct data paths relative to it
project_root = Path(__file__).parent.parent.parent
data_root = project_root / ".data"
DRUG_PROFILE_LOC = str(data_root / "bnf-drug-data/data/drug_profile_slugs.tsv")
DRUG_SPECIFIC_LOC = str(data_root / "bnf-drug-data/data/drugs/{drug_name}.json")


BRAND_DRUG_LOC = str(data_root / "bnf-drug-data/data/synonyms.tsv")

DEFAULT_THRESHOLD = 90  # Fuzzy matching threshold


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


def _match_ingredient_to_profile(
    ingredient: str, bnf_profiles: dict, threshold: int = DEFAULT_THRESHOLD
) -> tuple[str, bool]:
    """Helper function to match an ingredient to a BNF profile slug

    Returns:
        tuple[str, bool]: (matched slug or ingredient, success flag)
    """
    ingredient = ingredient.lower().strip()  # standardize to lower case

    if ingredient in bnf_profiles:
        # First check for a fast direct match
        return bnf_profiles[ingredient], True
    else:
        # Else find the best match among all brand names
        best_match = process.extractOne(ingredient, bnf_profiles.keys())
        if best_match[1] > threshold:
            return bnf_profiles[best_match[0]], True
        else:
            return ingredient, False


def ingredient_to_bnf_profile(
    ingredient: str, bnf_profiles: dict, threshold: int = DEFAULT_THRESHOLD
) -> str:
    """Resolve a single ingredient to a BNF profile slug"""
    matched_slug, success = _match_ingredient_to_profile(ingredient, bnf_profiles, threshold)
    if success:
        return matched_slug
    else:
        raise ValueError(f"Could not find a BNF profile slug match for {ingredient}")


def ingredients_to_bnf_profiles(
    ingredients: list, bnf_profiles: dict, threshold: int = DEFAULT_THRESHOLD
) -> str:
    """Resolve a list of ingredients to a BNF profile slug"""
    slug_components = []
    # Check for direct or fuzzy matches for each ingredient
    for i in ingredients:
        matched_slug, success = _match_ingredient_to_profile(i, bnf_profiles, threshold)
        slug_components.append(matched_slug)

    # Search for the combined slug
    search_term = " with ".join(slug_components)
    final_slug = process.extractOne(search_term, bnf_profiles.keys())[0]

    return bnf_profiles[final_slug]


def resolve_drug_profile(
    drug_name: str,
    synonyms: dict,
    bnf_profiles: dict,
    threshold: int = DEFAULT_THRESHOLD,
) -> str:
    """Resolve a drug name to a BNF profile slug"""

    drug_name = drug_name.lower().strip()  # standardize to lower case

    if drug_name in bnf_profiles:
        return bnf_profiles[drug_name]
    else:
        # if not found, try looking for ingredients or synonyms
        drug_ingredients = map_ingredients(drug_name, synonyms, threshold)

        try:
            if isinstance(drug_ingredients, str):
                return ingredient_to_bnf_profile(drug_ingredients, bnf_profiles, threshold)
            elif isinstance(drug_ingredients, list):
                if isinstance(drug_ingredients, list) and len(drug_ingredients) == 1:
                    return ingredient_to_bnf_profile(drug_ingredients[0], bnf_profiles, threshold)
                else:
                    return ingredients_to_bnf_profiles(drug_ingredients, bnf_profiles, threshold)
        except ValueError:
            raise ValueError(f"Could not find a BNF profile slug match for {drug_name}")


pot_names = [
    "indicationsAndDose",
    "drugAction",
    "cautions",
    "sideEffects",
    "allergyAndCrossSensitivity",
    "pregnancy",
    "hepaticImpairment",
    "renalImpairment",
    "preTreatmentScreening",
    "prescribingAndDispensingInformation",
    "patientAndCarerAdvice",
    "breastFeeding",
    "conceptionAndContraception",
    "contraIndications",
    "constituentDrugs",
    "directionsForAdministration",
    "effectOnLaboratoryTests",
    "exceptionsToLegalCategory",
    "handlingAndStorage",
    "importantSafetyInformation",
    # "interactants",
    "lessSuitableForPrescribing",
    "medicinalForms",
    # "monitoringRequirements",
    "nationalFunding",
    "palliativeCare",
    "professionSpecificInformation",
    "treatmentCessation",
    # "relatedTreatmentSummaries",
    "relatedNursePrescribersTreatmentSummaries",
    "unlicensedUse",
]


class DrugProfileContent(BaseModel):
    pot_name: str = Field(description="The name of the section")
    slug: str = Field(description="The slug of the section")
    contentFor: str = Field(description="The name of the drug")
    content: str = Field(description="The content of the section")


class DrugProfile(BaseModel):
    drug_name: str
    slug: str
    drug_classes: list[str] | None = Field(
        default=None, description="The classes this drug belongs to"
    )
    drug_content: dict[str, DrugProfileContent] | None = Field(
        default=None, description="The content of the drug"
    )
    drug_class_content: dict[str, dict[str, DrugProfileContent]] | None = Field(
        default=None, description="The content of the drug class"
    )

    @property
    def prompt(self) -> str:
        prompt: str = f"#### BNF Drug Profile - {self.drug_name}\n\n"

        if self.drug_classes:
            prompt += f"Information is provided for {self.drug_name} and the following classes to which {self.drug_name} belongs:\n"
            for drug_class in self.drug_classes:
                prompt += f"- {drug_class}\n"
            prompt += "\n"

            prompt += f"If the information is about {self.drug_name} then it won't be enclosed in any tags.\n"
            prompt += f"If the information is for a class, it's enclosed in <{self.drug_classes[0]}> tags, or equivalent tags for other classes.\n"
            prompt += f"Although information is provided at the class level, it still applies to {self.drug_name}.\n"

        for pot_name in pot_names:
            drug_content = self.drug_content.get(pot_name)
            drug_class_content = [
                x.get(pot_name) for x in self.drug_class_content.values() if x.get(pot_name)
            ]

            # There are two different behaviours for to now render the content.
            # If the drug class content exists, we need to specify that there is different content for each drug class.
            # If the drug class content does not exist, we can just return the content as normal.

            if drug_content or drug_class_content:
                pot_name_content = (
                    drug_content.pot_name if drug_content else drug_class_content[0].pot_name
                )
                prompt += f"\n##### {pot_name_content}\n"

            if drug_content:
                prompt += f"{drug_content.content}"

            if drug_class_content:
                for contents in drug_class_content:
                    prompt += (
                        f"<{contents.contentFor}>\n{contents.content}\n</{contents.contentFor}>\n"
                    )

        return prompt


def parse_html_content(html_content: str) -> str:
    """
    Converts HTML to Markdown, downgrading headings by a specified amount.
    Headings can be downgraded past h6, becoming bold (for level 7)
    or italic (for level 8 and beyond).
    """
    if not html_content:
        return ""

    # Iterate from h6 down to h1 to correctly replace without cascading issues
    # This ensures that an h1 downgraded to h2 isn't then re-processed when h2s are handled.
    for current_level in range(6, 0, -1):
        open_current_tag = f"<h{current_level}>"
        close_current_tag = f"</h{current_level}>"

        open_new_tag = "<strong>"
        close_new_tag = "</strong>\n"

        # Only perform replacement if the new tags are different from current ones
        if open_current_tag != open_new_tag:
            html_content = html_content.replace(open_current_tag, open_new_tag)
            html_content = html_content.replace(close_current_tag, close_new_tag)

    return markdownify(html_content)


def parse_indications_and_dose_content(pot_name: str, data: dict) -> DrugProfileContent:
    """
    Parse the drug content JSON and return a DrugProfileContent object
    with formatted HTML content.
    """

    # Extract the base information
    pot_name = data.get("potName", "")
    slug = data.get("slug", "")

    # Get the drug content section
    drug_content = data.get("drugContent", {})
    content_for = drug_content.get("contentFor", "")

    # Build the content HTML
    content_html = ""

    # Process indication and dose groups
    indication_dose_groups = drug_content.get("indicationAndDoseGroups", [])

    if indication_dose_groups:
        # Add therapeutic indications
        for group in indication_dose_groups:
            therapeutic_indications = group.get("therapeuticIndications", [])
            if therapeutic_indications:
                content_html += "Therapeutic Indications\n"
                for indication in therapeutic_indications:
                    indication_text = indication.get("indication", "")
                    if indication_text:
                        content_html += f"- {indication_text}\n"
                content_html += "\n"

            # Add patient groups and dosage information
            routes_patient_groups = group.get("routesAndPatientGroups", [])
            for route_group in routes_patient_groups:
                route = route_group.get("routeOfAdministration", "")
                patient_groups = route_group.get("patientGroups", [])

                if route and patient_groups:
                    for patient in patient_groups:
                        group_name = patient.get("detailedPatientGroup", "")
                        dose_statement = patient.get("doseStatement", "")

                        # Clean up HTML entities in the dose statement
                        dose_statement = re.sub(r"&nbsp;", " ", dose_statement)

                        if group_name and dose_statement:
                            content_html += f"{group_name} ({route}): {dose_statement}</p>\n"

    # Create and return the DrugProfileContent object
    return DrugProfileContent(
        pot_name=pot_name, slug=slug, contentFor=content_for, content=content_html
    )


def parse_pot_drug_content(pot_name: str, pot_content: dict) -> DrugProfileContent | None:
    drug_content = pot_content.get("drugContent")

    if drug_content:
        contentFor = drug_content.get("contentFor")
        content = parse_html_content(drug_content.get("content"))
        slug = drug_content.get("slug")
        if content:
            return DrugProfileContent(
                pot_name=pot_name, contentFor=contentFor, content=content, slug=slug
            )
    return None


def load_drug_profile(drug_profile: dict) -> DrugProfile:
    title = drug_profile.get("title")
    slug = drug_profile.get("slug")

    custom_parsers = {
        "indicationsAndDose": parse_indications_and_dose_content,
    }

    drug_class = []
    primaryClassification = drug_profile.get("primaryClassification")
    if primaryClassification:
        drug_class.append(primaryClassification.get("title"))
    secondaryClassifications = drug_profile.get("secondaryClassifications")
    if secondaryClassifications:
        drug_class.extend([x.get("title") for x in secondaryClassifications])

    drug_content = {}
    drug_class_content = defaultdict(dict)
    for pot_name in pot_names:
        pot_content = drug_profile.get(pot_name)

        parser = custom_parsers.get(pot_name, parse_pot_drug_content)

        if pot_content:
            # Parse the drug content
            pot_name_content = pot_content.get("potName")
            pot_drug_content = parser(pot_name_content, pot_content)
            if pot_drug_content:
                drug_content[pot_name] = pot_drug_content

            # Parse the drug class content, it comes as a list instead
            pot_drug_class_content = pot_content.get("drugClassContent")
            if pot_drug_class_content:
                for item in pot_drug_class_content:
                    drug_class_name = item.get("contentFor")
                    drug_class_content[drug_class_name][pot_name] = parser(
                        pot_name_content, {"drugContent": item}
                    )

    return DrugProfile(
        drug_name=title,
        slug=slug,
        drug_classes=drug_class,
        drug_content=drug_content,
        drug_class_content=drug_class_content,
    )


# Tool definitions
@tool
def get_bnf_drug_profile(
    drug_profile_loc: str = DRUG_PROFILE_LOC,
    drug_specific_loc: str = DRUG_SPECIFIC_LOC,
    brand_lookup: str = BRAND_DRUG_LOC,
    threshold: int = DEFAULT_THRESHOLD,
):
    synonyms = pd.read_csv(brand_lookup, index_col=0, sep="\t")["bnf_name"].to_dict()
    bnf_profiles = pd.read_csv(drug_profile_loc, index_col=0, sep="\t")["slug"].to_dict()

    async def execute(drug_name: str) -> str:
        """
        This function will return the drug profile for the given drug name if it exists in the British National Formulary (BNF) database.

        This is achieved by querying the BNF database.

        Information includes the drug class, indications, side effects, and more.

        Args:
            drug_name (str): The name of the drug to look up. Use single brand or chemical name for the drug. E.g 'Tagrisso', 'Co-codamol', 'Paracetamol'.

        Returns:
            The drug profile for the given drug names.
        """
        # find the drug profile page for the drug name
        try:
            drug_slug = resolve_drug_profile(drug_name, synonyms, bnf_profiles, threshold)
            # look up drug profile
            with open(drug_specific_loc.format(drug_name=drug_slug)) as file:
                profile = json.load(file)
            profile = load_drug_profile(profile["result"]["data"]["bnfDrug"])
            return profile.prompt
        except (ValueError, AttributeError):
            return f"Could not find a BNF profile slug match for {drug_name}, please continue with the next drug."

    return execute
