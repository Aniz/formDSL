"""
Generate java code from textX model using jinja2
template engine (http://jinja.pocoo.org/docs/dev/)
"""
from os import mkdir, walk
from os.path import exists, dirname, join
import jinja2
import pydot
from form_test import get_form_mm
from pprint import pprint
import shutil
import sys
import re
from textx.metamodel import metamodel_from_file
from textx.export import metamodel_export, model_export

def main(debug=False):

    this_folder = dirname(__file__)
    form_mm = get_form_mm(debug)

    # Build Event model from person.ent file
    form_model = form_mm.model_from_file(join(this_folder, 'form.form'))

    def javatype(s):
        """
        Maps type names from PrimitiveType to Java.
        """
        return {
                'integer': 'int',
                'string': 'String'
        }.get(s.name, s.name)

    # Create output folders
    srcgen_folder = join(this_folder, 'srcgen')
    if exists(srcgen_folder):
        shutil.rmtree(srcgen_folder)

    systemName = form_model.name
    
    general_folder = createFolder(this_folder, 'srcgen')
    general_form_folder = createFolder(general_folder, systemName.lower())
    dotFolder = createFolder(srcgen_folder, 'dot')
    createDotFiles(form_mm,form_model,dotFolder)

    # Get template folders
    templateFolder = join(this_folder, 'templates')
    
    # Initialize template engine.
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(this_folder),
        trim_blocks=True,
        lstrip_blocks=True)
    
    # Register filter for mapping event type names to Java type names.
    jinja_env.filters['javatype'] = javatype
    jinja_env.filters['upperfirst'] = upperfirst
    jinja_env.filters['splitName'] = splitName
    jinja_env.filters['remove'] = remove
    jinja_env.filters['append'] = append

    componentData = ""
    componentExtraData = ""
    componentDict = {}

    avaliableTypes = ["text","date","int","check","select"]
    
    #Get options from model
    for component in form_model.fields:
        if component.__class__.__name__ == 'Field':
            componentDict[component.name] = {"field":component}

    # for key,value in componentDict.items():
        generateFile(templateFolder,general_form_folder,'formTemplate.html',systemName,jinja_env,componentDict,"",systemName,".html")   
        shutil.copy(join(templateFolder,"form.css"),general_form_folder)   
    
def append(data):
    newA = []
    for k,v in data.items():
        if v["feature"].extend and v["feature"].extend.name not in newA:
            newA = newA + [v["feature"].extend.name]   
    return newA

def remove(data,item):
    return data.remove(item)


def upperfirst(x):
    return x[0].upper()+x[1:]

def splitName(fullName):
    return re.sub('([a-z])([A-Z])',"\g<1> \g<2>",fullName)

def split(fullName):
    return fullName.replace(" ","_")

def createDotFiles(form_mm,form_model,dotFolder):
    # Export to .dot file for visualization
    metamodel_export(form_mm, join(dotFolder, 'form_meta.dot'))
    # Export to .dot file for visualization
    model_export(form_model, join(dotFolder, 'form.dot'))

    (graph,) = pydot.graph_from_dot_file(join(dotFolder,'form_meta.dot'))
    graph.write_png(join(dotFolder,'form_meta.png'))
    
    (graph,) = pydot.graph_from_dot_file(join(dotFolder,'form.dot'))
    graph.write_png(join(dotFolder,'form.png'))
    
def copyCodeFile(src,dest,nameFile,jinja_env,var,extraVar,systemName):
    codeFileTemplate = jinja_env.get_template(join(src,nameFile+'.java'))
    with open(join(dest,"%s.java" % nameFile), 'w') as f:
            f.write(codeFileTemplate.render(data=var,extraData=extraVar,systemName=systemName))

def generateFile(src,dest,file,nameFile,jinja_env,var,extraVar,systemName,ext=".java"):
    codeFileTemplate = jinja_env.get_template(join(src,file))
    with open(join(dest,"%s" % nameFile+ext), 'w') as f:
            f.write(codeFileTemplate.render(data=var,extraData=extraVar,systemName=systemName))

def createFolder(dest,name):
    folder = join(dest, name)
    if not exists(folder):
        mkdir(folder)

    return folder

def generateCodeRecursively(src, dest,jinja_env,var,extraVar,statments,systemName,systemEmail,systemPass):
    for (dirpath,dirnames,filenames) in walk (src):
        for file in filenames:
            if file != "FeatureHelper.java":
                codeFileTemplate = jinja_env.get_template(join(src,file))
                with open(join(dest,file), 'w') as f:
                    f.write(codeFileTemplate.render(data=var,extraData=extraVar,statments=statments,systemName=systemName,systemEmail=systemEmail,systemPassword=systemPass))

def copy(src, dest):
    if exists(dest):
        shutil.rmtree(dest)

    try:
        shutil.copytree(src, dest)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            print('Directory not copied. Error: %s' % e)

if __name__ == "__main__":
    main()
