docker network create --attachable proj1_test

docker run --rm -p 8000:8000 --name SOMENAME --network qtlviewertest -v /Users/mvincent/work/qtlviewer/data/Attie_DO378_eQTL_viewer_v3.RData:/app/qtlapi/data/ppppppppppppppdata.RData -v /Users/mvincent/work/qtlviewer/data/ccfoundersnps.sqlite:/app/qtlapi/data/ccfounders.sqlite -v /Users/mvincent/work/qtlviewer/qtlapi/qtlapi.R:/app/qtlapi/qtlapi.R mattjvincent/qtlapi /app/qtlapi/qtlapi.R

Than in docker-compose.yml...

networks:
  default:
    external:
      name: qtlviewertest



# QTL Viewer
===================

This is a web application that renders QTL "type" data.  There are multiple components and moving parts, but 2 different main projects ake up the QTL Viewer.

## QTL API

The QTL API utilizes the following technology stack:

* [Docker](http://www.docker.com/) - Build, Ship, and Run Any App, Anywhere 
* [R](http://www.r-project.org/) - number cruncher
* [R/qtl2](http://kbroman.org/qtl2/) - Analysis 
* [Plumber](http://www.rplumber.io/) - Help turn R code into Web based API


The API generated is used by the QTL Web app.  The following API's are supplied:

#### /datasets

Description: The initial API called by QTL Web.  The data returned is dependent upon if the "dataType" is "mRNA", "protein", or "phenotype". The purpose of this API is to define and describe the datasets used in the viewer.

Parameters: None

Example response:
```
{"dataSets": [{
    "id": "some.dataset.identifier",
    "displayName": "Some Dataset",
    "dataType": "mRNA",
    "gene_ids": [
         "ENSMUSG00000000001",
         "ENSMUSG00000000028",
         "ENSMUSG00010203821",
         ...
    ],
    "protein_ids": [],
    "phenotypes" : [],
    "covarFactors":[{
        "column.name":"sex",
        "display.name":"Sex"
    }, {
        "column.name":"gen",
        "display.name":"Generation"}]
    },
    ...
    ],
    "ensemblVersion": 75,
    "numMarkers": 68433    
}
```

#### /lodscan

Description: Perform a LOD Scan.

Parameters:

| Parameter | Description |
| ------ | ------ |
| dataset | dataset identifier |
| id | the identifer to perform LOD scan on |
| regressLocal | TRUE to regress on local genotype, FALSE to not |
| nCores | number of cores to use |
| expand | TRUE to expand the JSON, FALSE to condense |

Example response (expanded):

```
{"result": [
    {"id":"1_4530778","chr":"1","pos":4.5308,"lod":1.688},
    {"id":"1_4533435","chr":"1","pos":4.5334,"lod":1.6709},
    ...
    {"id":"1_4536092","chr":"1","pos":4.5361,"lod":1.6539}
],
 "time":5.3
}
```

#### /foundercoefs

Description: Get founder coefficients.

Parameters:

| Parameter | Description |
| ------ | ------ |
| dataset | dataset identifier |
| id | the identifer to perform LOD scan on |
| chrom | the chromosome |
| regressLocal | TRUE to regress on local genotype, FALSE to not |
| blup | TRUE to perform Best Linear Unbiased Predictors  |
| center | TRUE to center around 0 |
| nCores | number of cores to use |
| expand | TRUE to expand the JSON, FALSE to condense |

Example response (expanded):

```
{"result":[{"id":"2_4292516","chr":"2","pos":4.2925,
            "A":0.012,"B":-0.0267,"C":0.0345,"D":0.1994,
            "E":0.1305,"F":-0.4769,"G":0.1217,"H":0.0055},
           {"id":"2_4337139","chr":"2","pos":4.3371,
            "A":0.0114,"B":-0.0267,"C":0.0343,"D":0.2,
            "E":0.1307,"F":-0.4769,"G":0.1218,"H":0.0055},
            ...
           {"id":"2_4369263","chr":"2","pos":4.3693,
            "A":0.012,"B":-0.0259,"C":0.0407,"D":0.2006,
            "E":0.1323,"F":-0.4783,"G":0.1134,"H":0.0052}
        ],
 "time":2.3
}
```

#### /expression

Description: Get the expression data.

Parameters:

| Parameter | Description |
| ------ | ------ |
| dataset | dataset identifier |
| id | the identifer to perform LOD scan on |

Example response:

```
{"data":[{"mouse_id":"F01","Sex":"F","Generation":"G4","Litter":2,
          "Diet":"hf","Coat.Color":"agouti","GenerationLitter":"G4_2",
          "expression":0.2243,"_row":"F01"},
          ...
         {"mouse_id":"F02","Sex":"F","Generation":"G4","Litter":2,
          "Diet":"hf","Coat.Color":"black","GenerationLitter":"G4_2",
          "expression":0.3498,"_row":"F02"}
         ],
 "time":2.3
}
```

#### /mediate

Description: Perform mediation analysis.

Parameters:

| Parameter | Description |
| ------ | ------ |
| dataset | dataset identifier |
| id | the identifer to perform LOD scan on |
| mid | marker identifier |
| expand | TRUE to expand the JSON, FALSE to condense |

Example response:

```
{"result":[{"gene_id":"ENSMUSG00000000001","symbol":"Gnai3",
            "chr":"3","pos":108.1267,"LOD":1.3625},
           {"gene_id":"ENSMUSG00000000028","symbol":"Cdc45",
            "chr":"16","pos":18.7962,"LOD":1.605},
           ...
           {"gene_id":"ENSMUSG00000000037","symbol":"Scml2",
            "chr":"X","pos":161.1877,"LOD":1.2535}
     ],
 "time":10.3
}
```

#### /snpassoc

Description: SNP Association Mappting

Parameters:

| Parameter | Description |
| ------ | ------ |
| dataset | dataset identifier |
| id | the identifer to perform LOD scan on |
| chrom | the chromosome |
| location | chromosomal location |
| windowSize | the window size, distance on each size of location |
| nCores | number of cores to use |
| expand | TRUE to expand the JSON, FALSE to condense |

Example response:

```
{"result":[{"snp":"rs245710663","chr":"1","pos":14.5001,
            "alleles":"G|C","sdp":64,"ensembl_gene":"",
            "csq":"intergenic_variant","index":1,"interval":147,
            "on_map":false,"lod":0.0015},
           {"snp":"rs263649601","chr":"1","pos":14.5002,
            "alleles":"C|T","sdp":64,"ensembl_gene":"",
            "csq":"intergenic_variant","index":1,"interval":147,
            "on_map":false,"lod":0.0015},
           ...
           {"snp":"rs32279922","chr":"1","pos":14.5004,
            "alleles":"C|T","sdp":153,"ensembl_gene":"",
            "csq":"intergenic_variant","index":3,"interval":147,
            "on_map":false,"lod":3.5395e-06}
         ],
 "time":11.1
}
```



## QTL Web

* [Docker](http://www.docker.com/) - Build, Ship, and Run Any App, Anywhere 
* [Python](http://www.python.org/) - Web framework
* [Celery](http://www.celeryproject.org/) - Distributed Task Queue
* [Redis](http://redis.io/) - Message Broker
* [Bootstrap 4](http://getbootstrap.com/) - HTML enhanced for web apps!



QTL Viewer uses a number of other projects to work properly:

* [Docker](http://www.docker.com/) - Build, Ship, and Run Any App, Anywhere 
* [Bootstrap 4](http://https://getbootstrap.com/) - HTML enhanced for web apps!
* [R](https://www.r-project.org/) - number cruncher
* [markdown-it] - Markdown parser done right. Fast and easy to extend.
* [Twitter Bootstrap] - great UI boilerplate for modern web apps
* [node.js] - evented I/O for the backend
* [Express] - fast node.js network app framework [@tjholowaychuk]
* [Gulp] - the streaming build system
* [Breakdance](http://breakdance.io) - HTML to Markdown converter
* [jQuery] - duh

And of course Dillinger itself is open source with a [public repository][dill]
 on GitHub.

### Installation

Dillinger requires [Node.js](https://nodejs.org/) v4+ to run.

Install the dependencies and devDependencies and start the server.

```
     {"result":[["1_100007442","1",100.0074,
                 "ENSMUSG00000028028","Alpk1","3",127.7255,6.1147],
                ["1_100078094","1",100.0781,
                 "ENSMUSG00000024727","Trpm6","19",18.8212,6.048],
                ...
                ["1_100148722","1",100.1487,
                 "ENSMUSG00000045725","Prr15","6",54.3286,6.5079],
               ],
      "time":4.9
     }
#'
#' Example of expand=TRUE result and dataset$dataType=mRNA:
#'     {"result":[{"marker":"1_100007442","chr":"1","pos":100.0074,
#'                 "gene_id":"ENSMUSG00000028028","symbol":"Alpk1",
#'                 "gene_chrom":"3","middle":127.7255,"lod":6.1147},
#'                {"marker":"1_100078094","chr":"1","pos":100.0781,
#'                 "gene_id":"ENSMUSG00000024727","symbol":"Trpm6",
#'                 "gene_chrom":"19","middle":18.8212,"lod":6.048},
#'                ...
#'                {"marker":"1_100148722","chr":"1","pos":100.1487,
#'                 "gene_id":"ENSMUSG00000045725","symbol":"Prr15",
#'                 "gene_chrom":"6","middle":54.3286,"lod":6.5079}
#'               ],
#'      "time":4.9
#'     }
```

For production environments...

```sh
$ npm install --production
$ NODE_ENV=production node app
```

### Plugins

Dillinger is currently extended with the following plugins. Instructions on how to use them in your own application are linked below.

| Plugin | README |
| ------ | ------ |
| Dropbox | [plugins/dropbox/README.md] [PlDb] |
| Github | [plugins/github/README.md] [PlGh] |
| Google Drive | [plugins/googledrive/README.md] [PlGd] |
| OneDrive | [plugins/onedrive/README.md] [PlOd] |
| Medium | [plugins/medium/README.md] [PlMe] |
| Google Analytics | [plugins/googleanalytics/README.md] [PlGa] |


### Development

Want to contribute? Great!

Dillinger uses Gulp + Webpack for fast developing.
Make a change in your file and instantanously see your updates!

Open your favorite Terminal and run these commands.

First Tab:
```sh
$ node app
```

Second Tab:
```sh
$ gulp watch
```

(optional) Third:
```sh
$ karma test
```
#### Building for source
For production release:
```sh
$ gulp build --prod
```
Generating pre-built zip archives for distribution:
```sh
$ gulp build dist --prod
```
### Docker
Dillinger is very easy to install and deploy in a Docker container.

By default, the Docker will expose port 8080, so change this within the Dockerfile if necessary. When ready, simply use the Dockerfile to build the image.

```sh
cd dillinger
docker build -t joemccann/dillinger:${package.json.version}
```
This will create the dillinger image and pull in the necessary dependencies. Be sure to swap out `${package.json.version}` with the actual version of Dillinger.

Once done, run the Docker image and map the port to whatever you wish on your host. In this example, we simply map port 8000 of the host to port 8080 of the Docker (or whatever port was exposed in the Dockerfile):

```sh
docker run -d -p 8000:8080 --restart="always" <youruser>/dillinger:${package.json.version}
```

Verify the deployment by navigating to your server address in your preferred browser.

```sh
127.0.0.1:8000
```

#### Kubernetes + Google Cloud

See [KUBERNETES.md](https://github.com/joemccann/dillinger/blob/master/KUBERNETES.md)


### Todos

 - Write MORE Tests
 - Add Night Mode

License
----

MIT


**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)


   [dill]: <https://github.com/joemccann/dillinger>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
   [john gruber]: <http://daringfireball.net>
   [df1]: <http://daringfireball.net/projects/markdown/>
   [markdown-it]: <https://github.com/markdown-it/markdown-it>
   [Ace Editor]: <http://ace.ajax.org>
   [node.js]: <http://nodejs.org>
   [Twitter Bootstrap]: <http://twitter.github.com/bootstrap/>
   [jQuery]: <http://jquery.com>
   [@tjholowaychuk]: <http://twitter.com/tjholowaychuk>
   [express]: <http://expressjs.com>
   [AngularJS]: <http://angularjs.org>
   [Gulp]: <http://gulpjs.com>

   [PlDb]: <https://github.com/joemccann/dillinger/tree/master/plugins/dropbox/README.md>
   [PlGh]: <https://github.com/joemccann/dillinger/tree/master/plugins/github/README.md>
   [PlGd]: <https://github.com/joemccann/dillinger/tree/master/plugins/googledrive/README.md>
   [PlOd]: <https://github.com/joemccann/dillinger/tree/master/plugins/onedrive/README.md>
   [PlMe]: <https://github.com/joemccann/dillinger/tree/master/plugins/medium/README.md>
   [PlGa]: <https://github.com/RahulHP/dillinger/blob/master/plugins/googleanalytics/README.md>
