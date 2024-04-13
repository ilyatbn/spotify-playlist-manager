from main import celery_app as app

# this will run monthly on the 10th.


@app.task(bind=True, name="discogs_processor")
def discogs_processor(self):
    pass
    # download the latest data dump from discogs to a temp volume (its gonna be LARGE I'd say over 100gigs)
    # https://discogs-data-dumps.s3.us-west-2.amazonaws.com/index.html?prefix=data/2024/
    # https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2024/discogs_20240401_releases.xml.gz
    # extract the file.
    # load it and parse the beast. i have no idea how, but i need to figure out how to diff it.
    # i saw there's a release id there but i need to know if i can start reading from a certain line or something.. idk.
    # parse every line, conver to json, extract release.genres, release.stypes, release._id and insert to mongo.
