import os
from neo4j import GraphDatabase
import openai
from dotenv import load_dotenv
from time import sleep
from string import Template

load_dotenv()

# OpenAI API configuration
openai.api_type = ""
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai_deployment = "chat-gpt35"

# Neo4j configuration & constraints
neo4j_url = os.getenv("NEO4J_CONNECTION_URL")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
gds = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))

root_folder = os.getenv("ROOT_FOLDER")

# Function to call the OpenAI API
def summarize_text(file_prompt, system_msg):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": file_prompt},
        ],
    )
    summary = completion.choices[0].message.content
    sleep(8)
    return summary

prompt_template = """
$ctext
"""

def generate_cypher_queries(root_folder):
    # Define the entry node as the last folder in the path
    entry_node = os.path.basename(root_folder)
    print(f"Entry node: {entry_node}")

    # Initialize the list of Cypher queries
    queries = []
    
    import urllib.parse

    # Create the entry node
    entry_node_path = "file://" + urllib.parse.quote(os.path.join(root_folder, entry_node))

    parameters = {
        'entry_node': entry_node,
        'entry_node_path': entry_node_path
    }
    query = f"CREATE (:{entry_node}:Folder {{name: $entry_node, path: $entry_node_path}})"

    queries.append((query, parameters))


    print(f"Created entry node query for {entry_node} with path {entry_node_path}")


    # Traverse the folder structure
    for dirpath, dirnames, filenames in os.walk(root_folder):
        print(f"Processing directory: {dirpath}")

        # Generate nodes and relationships for each directory
        for dirname in dirnames:
            parent_node = os.path.basename(dirpath)
            child_node = dirname
            child_node_path = "file://" + urllib.parse.quote(os.path.join(dirpath, dirname))

            parameters = {
                'child_node': child_node,
                'child_node_path': child_node_path
            }
            query = f"CREATE (:{child_node}:Folder {{name: $child_node, path: $child_node_path}})"
            queries.append((query, parameters))

            parameters = {
                'parent_node': parent_node,
                'child_node': child_node
            }
            query = "MATCH (a:Folder {name: $parent_node}), (b:Folder {name: $child_node}) CREATE (a)-[:CONTAINS]->(b)"

            queries.append((query, parameters))


            print(f"Added folder node and relationship for {child_node} with path {child_node_path}")

        # Generate nodes and relationships for each file
        for filename in filenames:
            if filename.endswith(".txt"):
                parent_node = os.path.basename(dirpath)
                file_node = os.path.splitext(filename)[0]
                file_path = os.path.join(dirpath, filename)
                file_node_path = "file://" + urllib.parse.quote(file_path)
                try:
                    with open(file_path, 'r') as file:
                        text = file.read().rstrip()
                        prompt = Template(prompt_template).substitute(ctext=text)
                        system_msg = f"Summarize the following text:"
                        summary = summarize_text(prompt, system_msg=system_msg)

                        parameters = {
                            'file_node': file_node,
                            'file_node_path': file_node_path,
                            'summary': summary
                        }
                        query = f"CREATE (:{file_node}:File {{name: $file_node, path: $file_node_path, summary: $summary}})"

                        queries.append((query, parameters))

                        parameters = {
                            'parent_node': parent_node,
                            'file_node': file_node
                        }
                        query = "MATCH (a:Folder {name: $parent_node}), (b:File {name: $file_node}) CREATE (a)-[:CONTAINS]->(b)"
                        queries.append((query, parameters))

                        print(f"Added file node and relationship for {file_node} with {file_node_path}")
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    return queries


def run_cypher_queries(cypher_statements):
    for i, (stmt, params) in enumerate(cypher_statements):
        print(f"Executing cypher statement {i + 1} of {len(cypher_statements)}")
        try:
            gds.execute_query(stmt, params)
        except Exception as e:
            with open("failed_statements.txt", "w") as f:
                # Include both the statement and parameters in the output
                f.write(f"{stmt} with params {params} - Exception: {e}\n")


def save_cypher_queries_to_file(queries, file_path):
    """
    Saves a list of Cypher queries with their embedded values to a file.

    :param queries: List of tuples containing Cypher queries and their parameters.
    :param file_path: Path to the file where queries will be saved.
    """
    with open(file_path, 'w') as file:
        for query, params in queries:
            # Manually replace placeholders with parameter values
            formatted_query = query
            for param_name, param_value in params.items():
                formatted_query = formatted_query.replace(f"${param_name}", f"'{param_value}'")

            file.write(formatted_query + '\n\n')


def print_cypher_queries_and_params(queries):
    """
    Prints a list of Cypher queries and their respective parameters.

    :param queries: List of tuples containing Cypher queries and their parameters.
    """
    for query, params in queries:
        # Print the query
        print("Query:\n" + query)
        # Print the parameters
        print("Parameters:\n" + str(params) + '\n')

# defined in .env file
queries = generate_cypher_queries(root_folder)

# Save the Cypher queries to a file
file_path = "cypher_queries.txt"
save_cypher_queries_to_file(queries, file_path)

print(f"Cypher queries saved to {file_path}")

run_cypher_queries(queries)


