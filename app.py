from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Configuración del endpoint de GraphDB
GRAPHDB_URL = 'http://Chavi-2.local:7200/repositories/Documentos'  # Cambia 'tu_repositorio' por el nombre de tu repositorio

# Consulta SPARQL de ejemplo para publicaciones con opción de filtro por año
def query_publications(year=None):
    query = """
    PREFIX schema: <http://schema.org/>
    SELECT ?headline ?url ?datePublished ?doi ?identifier
    WHERE {
      ?s1 a schema:CreativeWork ;
          schema:headline ?headline ;
          schema:identifier ?identifier .
      OPTIONAL { ?s1 schema:url ?url }
      OPTIONAL { ?s1 schema:datePublished ?datePublished }
      OPTIONAL { ?s1 schema:doi ?doi }
    """
    if year:
        query += f" FILTER((?datePublished) = '{year}')"
    query += " }"
    print(query)
    return execute_sparql_query(query)

# Consulta SPARQL para detalles de una publicación específica
def query_publication_details(identifier):
    query = """
    PREFIX schema: <http://schema.org/>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    PREFIX vivo: <http://vivoweb.org/ontology/core#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?headline
           ?url
           ?datePublished
           ?doi
           ?abstract
           ?citation
           ?volume
           ?identifier
           ?numberOfPages
           ?pageStart
           ?pageEnd
           ?authorName
           ?authorId
           ?areanombre
           ?subjectArea
    WHERE {
      ?s1 a schema:CreativeWork ;
          schema:headline ?headline .
      OPTIONAL { ?s1 schema:url ?url }
      OPTIONAL { ?s1 schema:datePublished ?datePublished }
      OPTIONAL { ?s1 schema:doi ?doi }
      OPTIONAL { ?s1 schema:abstract ?abstract }
      OPTIONAL { ?s1 schema:citation ?citation }
      OPTIONAL { ?s1 bibo:volume ?volume }
      OPTIONAL { ?s1 schema:identifier ?identifier }
      OPTIONAL { ?s1 schema:numberOfPages ?numberOfPages }
      OPTIONAL { ?s1 schema:pageStart ?pageStart }
      OPTIONAL { ?s1 schema:pageEnd ?pageEnd }
      OPTIONAL { ?s1 vivo:relatedBy ?related .
                  ?related vivo:relates ?author .
                  ?author foaf:name ?authorName ;
                          schema:identifier ?authorId }
      OPTIONAL { ?s1 vivo:hasSubjectArea ?subjectArea .
                 ?subjectArea rdfs:label ?areanombre }
      FILTER(?identifier = "{id}")
    }
    """.replace("{id}", identifier)
    return execute_sparql_query(query)


# Consulta SPARQL de ejemplo para autores
def query_authors():
    query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX schema: <http://schema.org/>
    SELECT ?name ?identifier ?affiliation
    WHERE {
      ?s3 a foaf:Person ;
          foaf:name ?name ;
          schema:identifier ?identifier .
      ?s2 a vivo:AuthorShip ;
          schema:affiliation ?affiliation ;
          vivo:relates ?s3 .
    }
    """
    return execute_sparql_query(query)

def query_years():
    query = """
    PREFIX schema: <http://schema.org/>
    SELECT DISTINCT ((?datePublished) as ?year)
    WHERE {
      ?s1 a schema:CreativeWork ;
          schema:datePublished ?datePublished .
    }
    ORDER BY ?year
    """
    results = execute_sparql_query(query)
    years = [result['year']['value'] for result in results]
    return years

# Consulta SPARQL de ejemplo para instituciones
def query_institutions():
    query = """
    PREFIX schema: <http://schema.org/>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    SELECT ?name ?url ?numberOfDocuments ?city ?country
    WHERE {
      ?s4 a schema:Organization ;
          schema:name ?name ;
          schema:url ?url ;
          schema:numberOfDocuments ?numberOfDocuments ;
          dbo:city ?city .
      ?s5 a dbo:City ;
          dbo:country ?country ;
          dbo:city ?city .
    }
    """
    return execute_sparql_query(query)

# Consulta SPARQL para publicaciones por autor
# Consulta SPARQL para publicaciones por autor usando el identificador
def query_publications_by_author(author_identifier):
    query = """
    PREFIX schema: <http://schema.org/>
    PREFIX bibo: <http://purl.org/ontology/bibo/>
    PREFIX vivo: <http://vivoweb.org/ontology/core#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?headline ?identifier ?url ?datePublished ?doi ?abstract ?citation ?volume ?pageStart ?pageEnd ?numberOfPages ?authorName ?authorId ?nombreAutor
    WHERE {
        ?s1 a schema:CreativeWork ;
            schema:headline ?headline ;
            schema:identifier ?identifier .
        OPTIONAL { ?s1 schema:url ?url }
        OPTIONAL { ?s1 schema:datePublished ?datePublished }
        OPTIONAL { ?s1 schema:doi ?doi }
        OPTIONAL { ?s1 schema:abstract ?abstract }
        OPTIONAL { ?s1 schema:citation ?citation }
        OPTIONAL { ?s1 bibo:volume ?volume }
        OPTIONAL { ?s1 schema:numberOfPages ?numberOfPages }
        OPTIONAL { ?s1 schema:pageStart ?pageStart }
        OPTIONAL { ?s1 schema:pageEnd ?pageEnd }
        ?s2 a vivo:AuthorShip .
        ?s2 vivo:relates ?author .
        
        ?author schema:identifier ?identifierAuthor .
        ?author foaf:name ?nombreAutor .


        FILTER(?identifierAuthor = "{id}")
    }
    """.replace("{id}", author_identifier)
    results = execute_sparql_query(query)

    author_name = results[0]['nombreAutor']['value'] if results else 'Unknown Author'
    publications = [result for result in results if 'headline' in result]

    return author_name, publications

def query_publications_by_subject_area(subject_area_id):
    query = """
    PREFIX schema: <http://schema.org/>
    PREFIX vivo: <http://vivoweb.org/ontology/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX scop: <http://scopus.org/data/>

    SELECT *
    WHERE {
    ?s1 a schema:CreativeWork ;
        schema:headline ?headline ;
        schema:identifier ?identifier ;
        vivo:hasSubjectArea ?subjectArea .
    ?subjectArea rdfs:label ?subjectAreaName .
    FILTER(?subjectArea = scop:{id})
    }

    """.replace("{id}", subject_area_id)
    return execute_sparql_query(query)


# Consulta SPARQL de ejemplo para temas
def query_topics():
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label
    WHERE {
      ?s7 a skos:Concept ;
          rdfs:label ?label .
    }
    """
    return execute_sparql_query(query)

# Función para ejecutar una consulta SPARQL
# Función para ejecutar una consulta SPARQL
def execute_sparql_query(query):
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'query': query}
    response = requests.post(GRAPHDB_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['results']['bindings']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/publications')
def publications():
    year = request.args.get('year')
    publications = query_publications(year)
    years = query_years()
    return render_template('publications.html', publications=publications, years=years)

@app.route('/publication/<identifier>')
def publication_details(identifier):
    data = query_publication_details(identifier)
    
    # Crear conjuntos para eliminar duplicados
    unique_authors = {(item['authorName']['value'], item['authorId']['value']) for item in data if 'authorName' in item and 'authorId' in item}
    unique_areas = {item['areanombre']['value'] for item in data if 'areanombre' in item}
    
    # Convertir conjuntos a listas para pasar a la plantilla
    authors_list = [{'name': author[0], 'id': author[1]} for author in unique_authors]
    areas_list = [{'name': area} for area in unique_areas]
    
    # Obtener detalles únicos de la publicación (el primer elemento es suficiente)
    publication_details = data[0] if data else {}

    return render_template('publications_details.html', 
                           publication=publication_details, 
                           authors=authors_list, 
                           areas=areas_list)
@app.route('/authors')
def authors():
    authors = query_authors()
    return render_template('authors.html', authors=authors)

@app.route('/author/<author_identifier>')
def author_publications(author_identifier):
    # Llamar a la función que obtiene tanto el nombre del autor como las publicaciones
    author_name, publications = query_publications_by_author(author_identifier)
    
    # Pasar tanto el nombre del autor como las publicaciones a la plantilla
    return render_template('author_publications.html', author_name=author_name, publications=publications)

@app.route('/institutions')
def institutions():
    institutions = query_institutions()
    return render_template('institutions.html', institutions=institutions)

@app.route('/topics')
def topics():
    topics = query_topics()
    return render_template('topics.html', topics=topics)

@app.route('/subject_area/<subject_area_id>')
def subject_area_publications(subject_area_id):
    # Consultar el área temática
    publications = query_publications_by_subject_area(subject_area_id)
    
    # Para obtener el nombre del área temática, podrías necesitar hacer otra consulta
    # Aquí asumo que la consulta `query_publications_by_subject_area` incluye el nombre del área.
    subject_area_name = ""  # Inicialmente vacío, debes obtener el nombre real de alguna manera.

    # Asumiendo que el nombre del área está incluido en las publicaciones, extraerlo:
    if publications:
        subject_area_name = publications[0].get('subjectAreaName', {}).get('value', 'Unknown Area')
    
    return render_template('subject_area_publications.html', publications=publications, subject_area_name=subject_area_name)


if __name__ == '__main__':
    app.run(debug=True)