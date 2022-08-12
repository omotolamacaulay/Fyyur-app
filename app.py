#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from operator import itemgetter 
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
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(150))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    shows = db.relationship("Show", backref="venue", lazy=True)

    def __repr__(self):
      return f'<Venue {self.id} {self.name} {self.city} {self.state} {self.address} {self.phone} {self.genres} {self.image_link} {self.facebook_link} {self.website_link} {self.talent} {self.seeking_description}>'

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(150))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    shows = db.relationship("Show", backref="artist", lazy=True)

    def __repr__(self):
      return f'<Artist {self.id} {self.name} {self.city} {self.state} {self.phone} {self.genres} {self.image_link} {self.facebook_link} {self.website_link} {self.seeking_venue} {self.seeking_description}>'

class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  venue_id= db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)
  artist_id= db.Column(db.Integer, db.ForeignKey("artists.id"), nullable=False)
  start_time= db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

  def __repr__(self):
    return f'<Artist {self.id} {self.venue_id} {self.artist_id} {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues = []
  artists = []
  venues = (
      Venue.query.with_entities(Venue.id, Venue.name, Venue.genres, Venue.image_link).order_by(Venue.date_created.desc()).limit(10).all()
  )
  artists = (
      Artist.query.with_entities(Artist.id, Artist.name, Artist.genres).order_by(Artist.date_created.desc()).limit(10).all()
  )
  # empty_venue_imgs = Venue.query.filter_by(image_link='').all()
  # for empty_venue_img in empty_venue_imgs:
  #   empty_venue_img.image_link="https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  return render_template("pages/home.html", venues=venues, artists=artists )


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.all()
  data = []
  locations = set()
  for venue in venues:
      locations.add((venue.city, venue.state))
  locations = list(locations)
  locations.sort(key=itemgetter(1, 0))

  present = datetime.now()
  for location in locations:
    venues_collection = []
    for venue in venues:
      if (venue.city == location[0]) and (venue.state == location[1]):

        shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming = 0
        for show in shows:
          if show.start_time > present:
              num_upcoming += 1

        venues_collection.append(
          {
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": num_upcoming,
          }
        )
    data.append({"city": location[0], "state": location[1], "venues": venues_collection})



  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get("search_term", "").strip()
  search_term=request.form.get('search_term')
  venues = Venue.query.filter_by(Venue.name.ilike('% + search_term + %')).all()
  response = {}
  response.count = len(venues)
  response.data = venues
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data=Venue.query.get(venue_id)
  all_shows= Show.query.filter_by(venue_id=venue_id).all()
  past_shows = []
  future_shows = []
  present = datetime.now()

  for single_show in all_shows:
    details = {
      "artist_id": single_show.artist_id,
      "artist_name": single_show.artist.name,
      "artist_image_link": single_show.artist.image_link,
      "start_time": format_datetime(str(single_show.start_time))
    }

    if single_show.start_time < present:
      past_shows.append(details)
    else:
      future_shows.append(details)

  data.upcoming_shows = future_shows
  data.past_shows= past_shows
  data.past_shows_count = len(past_shows)
  data.upcoming_shows_count = len(future_shows)
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
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link', 'https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60')
    facebook_link = request.form.get('facebook_link')
    website_link = request.form.get('website_link')
    talent = request.form.get('talent', default=False, type=bool)
    seeking_description = request.form.get('seeking_description', '')

    new_venue = Venue(
      name=name,
      city=city,
      state=state,
      address=address,
      phone=phone,
      genres=genres,
      image_link=image_link,
      facebook_link=facebook_link,
      website_link=website_link,
      talent=talent,
      seeking_description=seeking_description
    )
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
   try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue was successfully deleted!')
   except:
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
   finally:
    db.session.close()
 

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
   return redirect(url_for(index))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data= (
    Artist.query.all()
  )
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get("search_term", "").strip()
  search_term=request.form.get('search_term')
  artists = Artist.query.filter_by(Artist.name.ilike('% + search_term + %')).all()
  response = {}
  response.count = len(artists)
  response.data = artists
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data=Artist.query.get(artist_id)
  all_shows= Show.query.filter_by(artist_id=artist_id).all()
  past_shows = []
  future_shows = []
  present = datetime.now()

  for single_show in all_shows:
    details = {
      "venue_id": single_show.venue_id,
      "venue_name": single_show.venue.name,
      "venue_image_link": single_show.venue.image_link,
      "start_time": format_datetime(str(single_show.start_time))
    }

    if single_show.start_time < present:
      past_shows.append(details)
    else:
      future_shows.append(details)

  data.upcoming_shows = future_shows
  data.past_shows= past_shows
  data.past_shows_count = len(past_shows)
  data.upcoming_shows_count = len(future_shows)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
   
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link')
    facebook_link = request.form.get('facebook_link')
    website_link = request.form.get('website_link')
    seeking_venue = request.form.get('seeking_venue')
    seeking_description = request.form.get('seeking_description', '')

    artist = Artist.query.get(artist_id)

    artist.name = name,
    artist.city = city,
    artist.state = state,
    artist.phone = phone,
    artist.genres = genres,
    artist.image_link = image_link,
    artist.facebook_link = facebook_link,
    artist.website_link = website_link,
    seeking_venue = seeking_venue,
    artist.seeking_description = seeking_description

    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data =  venue.phone
  form.genres.data = venue.genres
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website_link
  form.seeking_talent.data = venue.talent
  form.seeking_description.data = venue.seeking_description
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link')
    facebook_link = request.form.get('facebook_link')
    website_link = request.form.get('website_link')
    talent = request.form.get('seeking_talent')
    seeking_description = request.form.get('seeking_description', '')

    venue = Venue.query.get(venue_id)

    venue.name = name,
    venue.city = city,
    venue.state = state,
    venue.phone = phone,
    venue.address = address 
    venue.genres = genres,
    venue.image_link = image_link,
    venue.facebook_link = facebook_link,
    venue.website_link = website_link,
    talent = talent,
    venue.seeking_description = seeking_description

    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
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
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    image_link = request.form.get('image_link', 'https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80')
    facebook_link = request.form.get('facebook_link')
    website_link = request.form.get('website_link')
    seeking_venue = request.form.get('seeking_venue', default=False, type=bool)
    seeking_description = request.form.get('seeking_description', '')

    new_artist = Artist(
      name=name,
      city=city,
      state=state,
      phone=phone,
      genres=genres,
      image_link=image_link,
      facebook_link=facebook_link,
      website_link=website_link,
      seeking_venue=seeking_venue,
      seeking_description=seeking_description
    )
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []

    shows = Show.query.order_by("id").all()

    for show in shows:
      artist = Artist.query.get(show.artist_id)
      venue = Venue.query.get(show.venue_id)
      show_detail = {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(str(show.start_time)),
      }
      data.append(show_detail)
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')

    new_show = Show(
      artist_id=artist_id,
      venue_id=venue_id,
      start_time=start_time
    )
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
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
