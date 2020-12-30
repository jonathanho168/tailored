This website has not yet been properly named. For now, the website will be called Tailored.

I have attempted to implement a crowdsourced recommendation algorithm for K-dramas a la Netflix.

Users will help create profiles for shows through the website. They will be asked to select which keywords apply to the drama and rate the drama from 0-10 for a number of categories. They will also note whether they liked the show, and therefore whether that show should be used in the creation of the user's profile.

These submissions will be averaged, and as user counts increase and submissions increase, the accuracy of each drama profile will increase.

This implementation is admittedly quite a slow one. There are countless SQL queries going on, modifying user profiles, drama profiles, user recommendations, etc. Each submission/return to "/" executes 680 SQL queries.

There are 8 tables in the database, listed and described below:

[Table] dramaprofile: averages of all submitted profiles, reaching a more correct profile as user submissions increase. The dummy variables in the webpage (either 0 or 1) are averaged, so that if a table entry says 0.71, for example, the relevant keyword is likely to apply to that drama.

[Table] dramas: a list of all K-dramas (english names) and some relevant information, i.e. main cast, airing network, years in which the show ran, and how many episodes. This was all pulled from Wikipedia in early December 2020.

[Table] liked: shows checked as "liked" are added here for every user. each entry consists of the drama title and the user to which this "liked" pertains. Having this distinction between "viewed" and "liked" allows us to get information about bad dramas, not just good ones.

[Table] ratings: averages of all ratings, similar to the "dramaprofile" table

[Table] recommend: stores each user's recommendations, which are calculated again every time the user loads "/". This allows for the user to have up-to-date recommendations based on all of the available drama profiles.

[Table] userprofile: stores each user's averages for each category based on shows they have watched, rated, and liked.

[Table] users: stores each user's name, username, hashed password, and time of account creation

[Table] viewed: what each user has ever seen. more comprehesive than the liked table. I could have simply created a column inside viewed for a boolean or a dummy variable in which the user notes whether he/she liked the show, but in my code, the program adds to the liked table before the viewed table, which doesn't work well with the dummy variable.

I also create a top 10. All of the ratings are combined to create a score for each drama, which is then used to choose the 10 most popular, or well-liked, drama.

The website has but two "pages". The home page presents the user with up to 30 recommendations. These recommendations are based on which drama profiles have the least squared difference from the user profile.

For example, if I had a drama that has the keywords "happy", "funny", and "exciting", and does not have the keywords "suspense", "wholesome", or "politics", I would be able to get a [1, 1, 1, 0, 0, 0] for that drama. Of course, the notation of a dictionary would entail that these are matched with each keyword, etc.; this is just for simplicity's sake.
My user profile is based on dramas I've watched before and is [0.2, 0.3, 0, 1, 1, 0].
Thus the sum of squared differences would be (1-0.2)^2 + (1-0.3)^2 + (1-0)^2 + (0-1)^2 + (0-1)^2 + (0-0)^2.
We sort the table and choose the dramas where 1. profiles already exist (so they're not just 0,0,0,0,0,0 which would do better than 1,1,1,1,1,1 in this case), 2. the drama wasn't rated poorly on average, and 3. the sum of squared differences are smallest.
We present 30 recommended in order of how likely they should like the content of the plot.

I do not implement search functions because Google and Wikipedia can provide much more information about a drama.
