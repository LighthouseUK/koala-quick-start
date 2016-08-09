# GFF MyGuild
Built using Project Koala and WebAppTools.

# Close Awards Tasks
- Publish results via pipeline, if applicable
- Change config to show that the awards are closed



# New Award Tasks
- Close previous awards, if necessary
- Clean open orders from system
- Switch config for new entry
- Update the dashboard download links
- Update categories (Map CURRENT_AWARD_MAP ot the necessary dict/set)
- Update logo links



## Important Notes
* The gffcompany module search has a field, `updated_timestamp`, which suffers from the [2038 problem](https://en.wikipedia.org/wiki/Year_2038_problem "2038 Problem Description").

## Setup
In order to install pycrypto on Windows you will need to install the [Visual C++ Compiler for Python 2.7](https://www.microsoft.com/en-us/download/details.aspx?id=44266).

There are two requirements.txt files included in the project.
`requirements_gae.txt` lists everything that needs to be installed
in order for the project to run on App Engine. Essentially, this is
the same list of dependencies as `requirements.txt` minus the
libraries that are already available on App Engine natively.

You would use `pip install -r requirements.txt` if you need to
resolve dependencies for your IDE while developing.

In order for the project to run on App Engine (or via the local SDK)
you will need to run `pip install -t thirdparty -r requirements_gae.txt` in your project root (alternately, specify the full install path if you are not in the project root).
This will install the required packages into the `thirdparty`. If this dir does not exist you will need to create it before running the above command.

If you do not have an `appengine_config.py` file you will need to create one.
Inside this file you will need to add the following lines:
`from google.appengine.ext import vendor
vendor.add('thirdparty')`.

To prevent the appcfg.py tool from uploading the setup files from the above pip install,
ensure you add the following to your `skip_files:` directive in `app.yaml`:

* `^grunt\.js`
* `.*node_modules/(.*/)?`
* `.*bower_components/(.*/)?`
* `^\.idea/.*`
* `^thirdparty/(.*)\.egg-info`
* `^thirdparty/(.*)\.dist-info`

Debugging `webapptools` is a little tricky. If you encounter a problem you will need to set a breakpoint in the relevant
`webapptools` file, inside the `thirdparty` dir of projects that implement it.

## Uploading
`appcfg.py update app.yaml`

`appcfg.py update_queues .`

### Multiple Accounts
You can specify which account to use when uploading by adding the `--no_cookies` and `--email=YOUR_EMAIL` arguments
`appcfg.py --no_cookies --email=EMAIL update app.yaml`

`appcfg.py --no_cookies --email=EMAIL update_queues .`

## Theme Install
* `npm install -g bower`
* `npm install -g gulp-cli`
* `npm install`
* `bower install`
* `gulp or gulp build or gulp build --production`

## Dev Server Database
I periodically backup my local datastore to GCS. If you have project access then you can download it from 
`/gff-uk/localdatastore`

To use it, run `dev_appserver.py` with the flag `--datastore_path=/path/to/datastore.db`, 
e.g. if you saved the datastore to the config folder: `--datastore_path=./config/datastore.db`