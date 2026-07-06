# Bug tracker
# "KeyError" for letterboxd_filmtitle
Got an error saying letterboxd_filmtitle doesn't exist for one of the entries. I think some of the RSS entries aren't normal movie reviews (maybe lists or something) so they don't have all the same fields. Fixed it by using .get() instead of just typing entry.fieldname, since .get() just returns None if the field isn't there instead of crashing.

