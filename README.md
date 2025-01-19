# commonology

A repository to support the development and growth of Quizitive, makers of the fun weekly social game Commonology!

Created by [Ted Moore](https://github.com/tedsmoore) and [Marc Schwarzschild](https://github.com/schwarzschild).

## Setup

### Postgres through Docker Compose

1. Install Docker.

    - [Docker](https://docs.docker.com/get-docker/)

2. Start Docker.
3. To start the DB, tun `docker compose up -d` in the root directory of the project. 
4. To load data into the database, run `docker compose exec -u postgres "/scripts/pg_update_docker_db.sh"`. This will use the latest database dump in your local pg_dumps folder to restore the db. You will need to create a dumpfile anytime you want to update the data.
5. When you're not developing, you can stop the DB with `docker compose down`.


[Server Installation Notes](server_files/README.md)<br>
[Setting up remote staging server](scripts/REMOTE_README.md)