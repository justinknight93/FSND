#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import datetime
import ast
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(db.String, nullable=False, default="[]")
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120), nullable=False, default="")
    phone = db.Column(db.String(120), nullable=False, default="")
    image_link = db.Column(db.String(500), nullable=False, default="")
    facebook_link = db.Column(db.String(120), nullable=False, default="")
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String, nullable=False, default="")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False, default="")
    genres = db.Column(db.String, nullable=False, default="[]")
    image_link = db.Column(db.String(500), nullable=False, default="")
    facebook_link = db.Column(db.String(120), nullable=False, default="")
    website = db.Column(db.String(120), nullable=False, default="")
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String, nullable=False, default="")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  for cityState in Venue.query.distinct(Venue.city,Venue.state):
    cityVenues = []
    for cityVenue in Venue.query.filter_by(city=cityState.city,state=cityState.state).order_by('id'):
      upcomingShows = Show.query.filter(and_(Show.venue_id==cityVenue.id,Show.start_time>datetime.datetime.now())).count()
      cityVenues.append({'id' : cityVenue.id, 'name' : cityVenue.name, 'num_upcoming_shows' : upcomingShows})
    data.append({'city' : cityState.city, 'state' : cityState.state, 'venues' : cityVenues})
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term=request.form.get('search_term', '')
  searchResultsCount=0
  data = []
  for searchVenue in Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).order_by('id'):
    upcomingShows = Show.query.filter(and_(Show.venue_id==searchVenue.id,Show.start_time>datetime.datetime.now())).count()
    data.append({'id' : searchVenue.id,'name' : searchVenue.name, 'num_upcoming_shows' : upcomingShows})
    searchResultsCount+=1
  
  response = {'count' : searchResultsCount, 'data' : data}
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id)

  upcomingShows = []
  upcomingCount = 0
  pastShows = []
  pastCount = 0

  for show in Show.query.filter(and_(Show.venue_id==venue.id,Show.start_time>datetime.datetime.now())):
    showArtist = Artist.query.get(show.artist_id)
    upcomingShows.append({
      "artist_id": showArtist.id,
      "artist_name": showArtist.name,
      "artist_image_link": showArtist.image_link,
      "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
    })
    upcomingCount+=1

  for show in Show.query.filter(and_(Show.venue_id==venue.id,Show.start_time<=datetime.datetime.now())):
    showArtist = Artist.query.get(show.artist_id)
    pastShows.append({
      "artist_id": showArtist.id,
      "artist_name": showArtist.name,
      "artist_image_link": showArtist.image_link,
      "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
    })
    pastCount+=1

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": ast.literal_eval(venue.genres),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": pastShows,
    "upcoming_shows": upcomingShows,
    "past_shows_count": pastCount,
    "upcoming_shows_count": upcomingCount,
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    _venue = Venue(
      name=request.form['name'], 
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      genres=json.dumps(request.form.getlist('genres')),
      facebook_link=request.form['facebook_link']
      )
    db.session.add(_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Venue could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return render_template('pages/home.html')
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully deleted!')
  except:
    flash('An error occurred. Venue could not be deleted.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return render_template('pages/home.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []

  for artist in Artist.query.order_by('id').all():
    data.append({'id' : artist.id, 'name' : artist.name})

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term', '')
  searchResultsCount=0
  data = []
  for searchArtist in Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).order_by('id'):
    upcomingShows = Show.query.filter(and_(Show.artist_id==searchArtist.id,Show.start_time>datetime.datetime.now())).count()
    data.append({'id' : searchArtist.id,'name' : searchArtist.name, 'num_upcoming_shows' : upcomingShows})
    searchResultsCount+=1
  
  response = {'count' : searchResultsCount, 'data' : data}
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  artist = Artist.query.get(artist_id)

  upcomingShows = []
  upcomingCount = 0
  pastShows = []
  pastCount = 0

  for show in Show.query.filter(and_(Show.artist_id==artist.id,Show.start_time>datetime.datetime.now())):
    showVenue = Venue.query.get(show.venue_id)
    upcomingShows.append({
      "venue_id": showVenue.id,
      "venue_name": showVenue.name,
      "venue_image_link": showVenue.image_link,
      "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
    })
    upcomingCount+=1

  for show in Show.query.filter(and_(Show.artist_id==artist.id,Show.start_time<=datetime.datetime.now())):
    showVenue = Venue.query.get(show.venue_id)
    pastShows.append({
      "venue_id": showVenue.id,
      "venue_name": showVenue.name,
      "venue_image_link": showVenue.image_link,
      "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
    })
    pastCount+=1

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": ast.literal_eval(artist.genres),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": pastShows,
    "upcoming_shows": upcomingShows,
    "past_shows_count": pastCount,
    "upcoming_shows_count": upcomingCount,
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artistData = Artist.query.get(artist_id)
  artist={
    "id": artistData.id,
    "name": artistData.name,
    "genres": ast.literal_eval(artistData.genres),
    "city": artistData.city,
    "state": artistData.state,
    "phone": artistData.phone,
    "website": artistData.website,
    "facebook_link": artistData.facebook_link,
    "seeking_venue": artistData.seeking_venue,
    "seeking_description": artistData.seeking_description,
    "image_link": artistData.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.get(artist_id)
    if request.form['name']: artist.name = request.form['name'] 
    if request.form['city']: artist.city = request.form['city'] 
    if request.form['state']: artist.state = request.form['state'] 
    if request.form['phone']: artist.phone = request.form['phone'] 
    if json.dumps(request.form.getlist('genres')): artist.genres = json.dumps(request.form.getlist('genres')) 
    if request.form['facebook_link']: artist.facebook_link = request.form['facebook_link'] 
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    flash('An error occurred. Artist could not be updated.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    if request.form['name']: venue.name = request.form['name'] 
    if request.form['city']: venue.city = request.form['city'] 
    if request.form['state']: venue.state = request.form['state'] 
    if request.form['address']: venue.address = request.form['address']
    if request.form['phone']: venue.phone = request.form['phone'] 
    if json.dumps(request.form.getlist('genres')): venue.genres = json.dumps(request.form.getlist('genres')) 
    if request.form['facebook_link']: venue.facebook_link = request.form['facebook_link'] 
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    flash('An error occurred. Vrtist could not be updated.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  
  try:
    _artist = Artist(
      name=request.form['name'], 
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      genres=json.dumps(request.form.getlist('genres')),
      facebook_link=request.form['facebook_link']
      )
    db.session.add(_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Artist could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data=[]

  for show in Show.query.all():
    showVenue = Venue.query.get(show.venue_id)
    showArtist = Artist.query.get(show.artist_id)
    data.append({
      "venue_id": showVenue.id,
      "venue_name": showVenue.name,
      "artist_id": showArtist.id,
      "artist_name": showArtist.name,
      "artist_image_link": showArtist.image_link,
      "start_time": show.start_time.strftime("%d/%m/%Y, %H:%M")
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    _show = Show(
      venue_id=request.form['venue_id'], 
      artist_id=request.form['artist_id'],
      start_time=datetime.datetime.strptime(request.form['start_time'], '%Y-%m-%d %H:%M:%S'),
      )
    db.session.add(_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
