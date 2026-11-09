"""Entry point 4: build the knowledge base, then read each procedure back from it."""

from config import config
from knowledge.chunk_splitting import build_chunk_records, split_documents_into_sections
from knowledge.pdf_extraction import extract_text_from_directory
from knowledge.procedure_reading import read_customer_notice_exemption, read_procedure_deadlines
from knowledge.vector_index import build_vector_index, open_vector_index


def main():
    """Build the store from scratch and prove each procedure answers from its own document."""
    print("building the incident response knowledge index")
    documents = extract_text_from_directory(config.DOCS_DIRECTORY)
    sections = split_documents_into_sections(documents)
    chunks = build_chunk_records(sections, config.CHUNK_SIZE_CHARACTERS,
                                 config.CHUNK_OVERLAP_CHARACTERS)
    stored = build_vector_index(chunks, config.VECTOR_STORE_DIRECTORY,
                                config.VECTOR_COLLECTION_NAME)
    print(f"    documents read:  {len(documents)}")
    print(f"    sections found:  {len(sections)}")
    print(f"    passages stored: {stored}")
    print(f"    store location:  {config.VECTOR_STORE_DIRECTORY}")

    collection = open_vector_index(config.VECTOR_STORE_DIRECTORY, config.VECTOR_COLLECTION_NAME)
    failures = []
    print("\nreporting deadlines, read back from each procedure's own document")
    for procedure_code in config.PROCEDURE_OPTIONS:
        own_document = config.PROCEDURE_DOCUMENT_BY_CODE[procedure_code]
        try:
            reading = read_procedure_deadlines(collection, procedure_code)
        except ValueError as error:
            failures.append(str(error))
            print(f"  {procedure_code}   FAILED: {error}")
            continue
        print(f"  {procedure_code}   {', '.join(reading['source_documents'])}")
        if reading["source_documents"] != [own_document]:
            failures.append(f"{procedure_code} was read from {reading['source_documents']}")
        for milestone in reading["milestones"]:
            print(f"      {milestone['milestone']:<50} within {milestone['hours']} hours of "
                  f"{milestone['clock_start_phrase']} ({milestone['clock_start_column']})")
        for filed in reading["filed_milestones"]:
            print(f"      {filed['milestone']:<50} {filed['months']} month(s) after the "
                  f"{filed['after_milestone']} is filed")

    try:
        exemption = read_customer_notice_exemption(collection,
                                                   config.PROCEDURE_EU_PERSONAL_DATA_BREACH)
        for state in exemption["exempt_protection_states"]:
            print(f"\ncustomers need not be told where the data protection state is {state}   "
                  f"{', '.join(exemption['source_documents'])}")
    except ValueError as error:
        failures.append(str(error))
        print(f"\nthe customer-notice exemption could not be read: {error}")

    if failures:
        print("\nBUILD FAILED: " + "; ".join(failures))
    else:
        print("\nevery procedure was read from its own document")
    return stored


if __name__ == "__main__":
    main()
