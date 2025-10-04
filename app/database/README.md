# Database

This python module is used to interact with the on-disk/docker file-based sqlite3 database.
It stores the papers and workflows (projects) for the frontend but doesn't implement its own endpoints;
the python `FastAPI` at `/app/api/main.py` handles the connections.

# Functionality

The module uses a on-disk file to store the data in a SQL database using the `sqlite3` python library.
Each request then accesses the database and the underlying file is stored automatically by `sqlite3` once no thread is using it anymore
(calling `sqlite.connect` uses an existing connection, if possible, even from another thread).
The requests that modify the database are all put into transactions individually.

# Problems

## The Papers from the collection aren't deleted!

The basic problem is that `sqlite3` doesn't offer an option to make the database have a (linerizable consistency)[https://en.wikipedia.org/wiki/Linearizability],
meaning that if one client writes something to the database, another client, that reads the database at a later date doesn't necessarily read it
(they might read an older version of the data there).

Because each request is done in a seperate connection to the database, each request is considered a different client, so if something is written to the database
(for example, "please delete the paper with this ID from my saved papers") and then another request comes (for example, "what papers do I have saved"),
the first write isn't necessarily reflected if the time between write and read was sufficiently short (As per experiments, around 5 seconds).

The simple solution is to not reload right after removing a paper (or modifying the database in some other way) and instead wait a bit.

The better solution is to somehow find a way to get `sqlite3` to have linearizable consistency,
but I haven't found a way to achieve this in a way that is compatible with a FastAPI service.
This means that, in order to remove this error, it is probably necessary so switch to another database.
Because the "frontend and backend" for the access to papers and workflows are already seperated, it shouldn't be very difficult.
