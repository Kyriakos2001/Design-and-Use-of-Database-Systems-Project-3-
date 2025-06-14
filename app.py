# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import sys,os

from lib import pymysql
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
import pymysql
import settings

def connection():
    ''' User this function to create your connections '''    
    con = pymysql.connect(host='127.0.0.1', port=33077, user='root', passwd='Kyriakos44', db='moviestar' ) #update with your settings
    
    return con

def updateRank(rank1, rank2, movieTitle):

    # Create a new database connection
    con = connection()

    # Create a cursor on the connection
    cur = con.cursor()

    # Validate rank inputs
    try:
        # Attempt to convert rank inputs to floats
        rank1 = float(rank1)
        rank2 = float(rank2)
    except:
        # Return error status if conversion fails
        return [("status",),("error",),]

    # Ensure ranks are within the valid range (0 to 10)
    if not (0 <= rank1 <= 10 and 0 <= rank2 <= 10):
        # Return error status if ranks are out of bounds
        return [("status",),("error",),]

    # SQL query to fetch movie rank by title
    sql = "SELECT m.rank FROM movie m WHERE m.title = '%s'" % (movieTitle,)

    try:
        # Execute the query
        cur.execute(sql)
        # Fetch all results
        results = cur.fetchall()

        # Check if the movie title is unique
        if len(results) != 1:
            # Return error status if there are more that one movies with this title
            return [("status",),("error",),]
        
        # Extract rank from the result
        original_rank = results[0][0]
        
    except:
        # Return error status if query execution fails
        return [("status",),("error",),]

    # Calculate new rank based on original rank
    if original_rank is None:
        # If original rank is None, calculate the average of rank1 and rank2
        new_rank = (rank1 + rank2) / 2
    else:
        # Otherwise, calculate the average of rank1, rank2, and original rank
        new_rank = (rank1 + rank2 + original_rank) / 3

    # SQL query to update the movie's rank
    sql = "UPDATE movie m SET m.rank = '%d' WHERE m.title = '%s'" % (new_rank, movieTitle)

    try:
        # Execute the update query
        cur.execute(sql)
        # Commit the transaction
        con.commit()
        # Return success status
        return [("status",),("ok",),]

    except:
        # Rollback the transaction if update fails
        con.rollback()
        # Return error status
        return [("status",),("error",),]

    finally:
        # Close cursor and connection
        cur.close()
        con.close()

def colleaguesOfColleagues(actorId1, actorId2):
    
    # Create a new database connection
    con = connection()

    # Create a cursor on the connection
    cur = con.cursor()
    
    try:
        # SQL query to find pairs of colleagues
        find_pairs_sql = """
        SELECT c.actor_id AS Actor_C, d.actor_id AS Actor_D
        FROM role a, role c, role b, role d
        WHERE a.actor_id = %s 
        AND c.actor_id != a.actor_id 
        AND d.actor_id != b.actor_id 
        AND c.actor_id != b.actor_id 
        AND d.actor_id != a.actor_id 
        AND a.movie_id = c.movie_id 
        AND b.actor_id = %s 
        AND b.movie_id = d.movie_id 
        AND EXISTS (
            SELECT 1
            FROM role rc, role rd
            WHERE rc.actor_id = c.actor_id 
            AND rd.actor_id = d.actor_id 
            AND rc.movie_id = c.movie_id 
            AND rd.movie_id = d.movie_id
        )
        """

        # SQL query to find movies for each pair
        find_movies_sql = """
        SELECT m.title AS Movie_title
        FROM role r1, role r2, movie m
        WHERE r1.actor_id = %s 
        AND r2.actor_id = %s 
        AND r1.actor_id != r2.actor_id 
        AND r1.movie_id = r2.movie_id 
        AND r1.movie_id = m.movie_id
        ORDER BY m.title DESC
        """

        # Execute the query to find pairs of colleagues
        cur.execute(find_pairs_sql, (actorId1, actorId2))
        pairs_result = cur.fetchall()

        # If no pairs found, return an empty list
        if not pairs_result:
            return [("status",),("error",),]

        # Initialize the output list with a header row
        output = [("movieTitle", "colleagueOfActor1", "colleagueOfActor2", "actor1","actor2")]
        processed_pairs = set()

        # Iterate through each pair of colleagues
        for pair in pairs_result:
            Actor_C = pair[0]
            Actor_D = pair[1]

            # Sort the actor IDs within the pair
            sorted_pair = tuple(sorted([Actor_C, Actor_D]))

            # Check if the sorted pair has already been processed
            if sorted_pair in processed_pairs:
                continue

            # Execute the query to find movies for the pair
            cur.execute(find_movies_sql, (Actor_C, Actor_D))
            movie_results = cur.fetchall()

            # If no movies found, continue to the next pair
            if not movie_results:
                continue

            # Iterate through each movie and append to the output list
            for movie_row in movie_results:
                Movie_title = movie_row[0]
                output.append((Movie_title, Actor_C, Actor_D, actorId1, actorId2))

            # Add the sorted pair to the set of processed pairs
            processed_pairs.add(sorted_pair)

        return output

    except Exception as e:
        # Handle exceptions, print the error, and rollback the transaction
        print(f"Error: {e}")
        con.rollback()
        return []

    finally:
        # Close the cursor and connection in the finally block
        cur.close()
        con.close()

def actorPairs(actorId):
    try:
        # Create connection to the database
        con = connection()
        
        # Create a cursor on the connection
        cur = con.cursor()
        
        # Step 1: Find genres of the input actor
        sql = "SELECT DISTINCT mg.genre_id FROM movie_has_genre mg, role r WHERE mg.movie_id = r.movie_id AND r.actor_id = %s" % (actorId,)
        
        # Execute the query
        cur.execute(sql)
        
        # Fetch the results and store the genres in a set
        actor_genres = set(row[0] for row in cur.fetchall())
        
        # Check if the actor has played in at least 7 genres
        if len(actor_genres) < 7:
            return [("status", "error")]  # Input actor not qualified
        
        # Step 2: Find actors who have played in movies with the input actor and the genres of those movies
        sql = '''SELECT r2.actor_id, mg.genre_id 
                 FROM role r1, role r2, movie_has_genre mg 
                 WHERE r1.movie_id = r2.movie_id 
                 AND r1.movie_id = mg.movie_id 
                 AND r1.actor_id = %s 
                 AND r1.actor_id != r2.actor_id''' % (actorId,)
        
        # Execute the query
        cur.execute(sql)
        
        # Initialize dictionaries to store genres for each actor
        actor_genre_dict = {}
        common_genres_dict = {}
        
        # Process the query results
        for actor, genre in cur.fetchall():
            # If actor is not in the dictionary, initialize their genre sets
            if actor not in actor_genre_dict:
                actor_genre_dict[actor] = set()
                common_genres_dict[actor] = set()
            
            # Add the genre to both dictionaries
            actor_genre_dict[actor].add(genre)
            common_genres_dict[actor].add(genre)
        
        #Join actor IDs into a comma-separated string that can be used in the SQL query.
        actor_ids = ','.join(str(actor_id) for actor_id in actor_genre_dict.keys())

        # Step 3: Find genres of the other actors outside of movies they played together
        sql = "SELECT r.actor_id, mg.genre_id FROM role r, movie_has_genre mg WHERE r.movie_id = mg.movie_id AND r.actor_id IN (%s) AND r.movie_id NOT IN (SELECT movie_id FROM role WHERE actor_id = %s)" % (actor_ids, actorId)
        
        # Execute the query
        cur.execute(sql)
        
        # Process the additional genres for each actor
        for actor, genre in cur.fetchall():
            actor_genre_dict[actor].add(genre)
        
        # Step 4: Filter actors based on the conditions
        result = [("actorId",)]
        for actor, genres in actor_genre_dict.items():
            # Check if the actor has at least 7 common genres and no overlapping genres outside the common movies
            if len(common_genres_dict[actor]) >= 7 and actor_genres.isdisjoint(genres - common_genres_dict[actor]):
                result.append((actor,))
        
        # If no actors meet the criteria, return an error status
        if len(result) == 1:
            return [("status", "error")]
        
        # Return the list of qualifying actors
        return result
    
    except Exception as e:
        # Handle any exceptions by returning an error status
        return [("status", "error")]
    
    finally:
        # Close the cursor and connection to free up resources
        cur.close()
        con.close()
    
def selectTopNactors(n):
    # Create a new connection
    con = connection()

    # Create a cursor on the connection
    cur = con.cursor()

    try:
        # Step 1: Retrieve all genres from the database
        sql = "SELECT genre_id, genre_name FROM genre"
        cur.execute(sql)
        genres = cur.fetchall()
        
        # Create a dictionary to map genre IDs to genre names
        genre_dict = {row[0]: row[1] for row in genres}

        # Step 2: Retrieve all roles (actor-movie relationships) from the database
        sql = "SELECT actor_id, movie_id FROM role"
        cur.execute(sql)
        roles = cur.fetchall()
        
        # Initialize dictionaries to store movie counts for each actor and their associated movies
        actor_movie_count = {}
        actor_movies = {}

        # Iterate through the roles and count movies for each actor
        for actor_id, movie_id in roles:
            if actor_id not in actor_movie_count:
                # If actor is not in the dictionary, initialize their movie count and movie set
                actor_movie_count[actor_id] = 0
                actor_movies[actor_id] = set()
            actor_movie_count[actor_id] += 1  # Increment the movie count for the actor
            actor_movies[actor_id].add(movie_id)  # Add the movie to the actor's set

        # Step 3: Retrieve movie genres from the database
        sql = "SELECT movie_id, genre_id FROM movie_has_genre"
        cur.execute(sql)
        movie_genres = cur.fetchall()
        
        # Initialize a dictionary to store genres for each movie
        movie_genre_dict = {}
        for movie_id, genre_id in movie_genres:
            if movie_id not in movie_genre_dict:
                movie_genre_dict[movie_id] = set()
            movie_genre_dict[movie_id].add(genre_id)

        # Step 4: Count the number of movies for each actor in each genre
        genre_actor_count = {genre: {} for genre in genre_dict.values()}

        # Iterate through actors and their associated movies
        for actor_id, movies in actor_movies.items():
            for movie_id in movies:
                if movie_id in movie_genre_dict:
                    for genre_id in movie_genre_dict[movie_id]:
                        genre_name = genre_dict[genre_id]
                        if actor_id not in genre_actor_count[genre_name]:
                            genre_actor_count[genre_name][actor_id] = 0
                        genre_actor_count[genre_name][actor_id] += 1

        # Step 5: Prepare the final list of top N actors for each genre
        n = int(n)
        top_actors_list = [("genreName", "actorID", "numberOfMovies")] 

        # Iterate through genres and their associated actors
        for genre, actors in genre_actor_count.items():
            # Sort actors based on the number of movies they've appeared in for the genre
            sorted_actors = sorted(actors.items(), key=lambda x: x[1], reverse=True)[:n]
            # Append top N actors for the genre to the final list
            for actor_id, movie_count in sorted_actors:
                top_actors_list.append((genre, actor_id, movie_count))

        return top_actors_list

    except Exception as e:
        # Return an error status in case of any exceptions
        return [("status", "error")]

    finally:
        # Close cursor and connection
        cur.close()
        con.close()

def traceActorInfluence(actorId):
    # Create a new connection
    con=connection()

    # Create a cursor on the connection
    cur=con.cursor()


    return [("influencedActorId",),]