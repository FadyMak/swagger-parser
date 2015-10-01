import re
from pathlib import Path

################################################
API_PATH = '../api/'
################################################

def main():
    # sequentially executes the annotation extraction and processing steps
    api_annotated_files = get_api_annotated_files()
    logger(str(api_annotated_files))

    # for each file we parse the classes and, in turn, it's methods
    for source_file in api_annotated_files:
        parse_class(source_file)

def parse_class(source_file):
    # logic to extract the class data and associated annotations

    # find api declaration associated to the class
    with source_file.open() as curr_file:
        code = curr_file.read()

    matches = re.search('(/\*api(.*?)(public|private|protected|)(.*?)class(.*?){)', code, re.DOTALL)

    class_annotations = matches.group(0)
    logger("-------------------------------")
    path = parse_path(class_annotations)
    logger(path)
    logger("-------------------------------")
    produces = parse_produces(class_annotations)
    logger(produces)
    logger("-------------------------------")
    api = parse_api(class_annotations)
    logger(api)
    logger("-------------------------------")
    parse_methods(code)

def parse_methods(code):
    # takes in a source file and extracts all the method annotations

    # regex for matching all /*api ... */ INCLUDING the method signature
    pattern = re.compile('/\*api(.*?)\*/(.*?){', re.DOTALL)
    # matches is a list containing 2-tuple
    #   - first is everything between /*api ... */
    #   - seconds is the method signature and potentially any other non-API
    #     tags such as @Override or @Deprecated
    annotation_matches = pattern.findall(code)

    for annotation in annotation_matches:
        # make sure we only parse methods and not classes by detecting the
        # @GET|POST|PUT|DELETE... tag in the annotation
        http_method = parse_http_method(annotation[0])
        if http_method:
            method_name, method_return = method_sig_analyzer(annotation[1])
            path = parse_path(annotation[0])
            api_operations = parse_api_operation(annotation[0])
            # logger(api_operations)
            # logger(method_name + '   ' + method_return)
            api_responses = parse_api_responses(annotation[0])
            logger(api_responses)
            logger("-------------------------------")

def method_sig_analyzer(signature_param):
    # this method analyzes a method signature and returns its constituents

    # selection of the approprite regex is based on whether a static modifier
    # exists in the method signature or not
    method_sig_regex = re.compile('(public|private|protected)\s([^\s]+)\s(\w+)', re.DOTALL)

    if 'static' in signature_param:
        signature = signature_param.replace(' static', '')
    else:
        signature = signature_param

    method_sig_raw = signature.replace('\n', ' ')
    method_sig_matches = method_sig_regex.search(method_sig_raw)

    method_name = method_sig_matches.group(3)
    method_return = method_sig_matches.group(2)

    return method_name, method_return

def parse_api_operation(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiOperation tag body

    key_val_regex = re.compile('(\w+)\s*?=\s*?"(.*?)"', re.DOTALL)
    parts = re.split('\*\s*?@', annotations)
    for item in parts:
        if 'ApiOperation' in item:
            api_op_regex = re.compile('ApiOperation\((.*)\)', re.DOTALL)
            matches = api_op_regex.search(item)
            key_val_annotations = matches.group(1)

            key_val_list = key_val_regex.findall(key_val_annotations)

    return dict(key_val_list)

def parse_api_responses(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiResponses tag body

    api_responses = []

    key_val_regex = re.compile('(\w+)\s*?=\s*?(".*?"|[0-9]{3})', re.DOTALL)
    inner_tag_regex = pattern = re.compile('@ApiResponses\((.*?}).*?\)', re.DOTALL)

    inner_tag = inner_tag_regex.search(annotations)
    response_annotations = inner_tag.group(1)

    single_res_regex = re.compile('ApiResponse\((.*?)\)', re.DOTALL)
    res_list = single_res_regex.findall(response_annotations)

    for res in res_list:
        key_val_list = key_val_regex.findall(res)
        api_responses.append(key_val_list)

    return dict(api_responses)

def parse_http_method(annotations):
    # takes an annotations string and returns the extracted HTTP method
    # GET/POST/PUT/DELETE/...

    matches = re.search('@(GET|POST|PUT|DELETE|OPTIONS|HEAD|PATCH)', annotations, re.DOTALL)
    if matches:
        return matches.group(1)
    else:
        return None

def parse_path(annotations):
    # takes a string containing a subset of the annotations and returns the
    # value of the path variable
    matches = re.search('@Path\("(.*?)"\)', annotations, re.DOTALL)
    if matches:
        return matches.group(1)
    else:
        return ''

def parse_produces(annotations):
    # takes a string containing a subset of the annotations and returns a list
    # containing the types it produces
    matches = re.search('@Produces\(\{(.*?)\}\)', annotations, re.DOTALL)
    inner_content = matches.group(1)

    # strip away white space and double quotation marks (")
    produces = [x.strip('" ') for x in inner_content.split(",")]

    return produces

def parse_api(annotations):
    # takes a string containing a subset of the annotations and returns a dict
    # containing the the key-value pair (value: '..', description: '..')

    api_result = []

    matches = re.search('@Api\((.*?)\)', annotations, re.DOTALL)
    inner_content = matches.group(1)

    # split by comma ONLY if the quotation marks (") match up
    # this essentially allows commas within quotations as opposed to solely limiting
    # the use of commas as an attribute delimiter

    key_val_regex = re.compile('(\w+)\s*?=\s*?"(.*?)"', re.DOTALL)
    key_val_list = key_val_regex.findall(inner_content)

    return dict(key_val_list)

def get_api_annotated_files():
    # returns a list of files that have been annotated with @Api signifying
    # that the file is a Swagger resource, as well as the start index of @Api(...)
    file_list = []

    # get the list of all the files in the api directory
    # all_files = [ abspath(f) for f in listdir(API_PATH) if isfile(join(API_PATH,f)) ]
    path = Path(API_PATH)
    all_files = [ f.resolve() for f in list(path.rglob('*')) if f.is_file() ]

    # filter the files for ones containing the @Api declaration
    # eg: @Api(value = "/pet", description = "Operations about pets")
    for curr_file in all_files:
        with curr_file.open() as source_file:
            code = source_file.read()
            annotation_exists = code.find("@Api(")

        if (annotation_exists != -1):
            file_list.append(curr_file)

    return file_list

def logger(msg):
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

    print(OKBLUE + str(msg) + ENDC)

if __name__ == '__main__':
    main()
