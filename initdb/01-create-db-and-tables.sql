CREATE TABLE IF NOT EXISTS users (
    UserID SERIAL PRIMARY KEY,
    UserName VARCHAR(50) UNIQUE NOT NULL,
    UserPassword VARCHAR(100) NOT NULL,
    UserType VARCHAR(20) NOT NULL DEFAULT 'bidder',
    Classification VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS bookings(
    BookingID SERIAL PRIMARY KEY,
    BidderName varchar(40) NOT NULL,
    WorkerName varchar(40) NOT NULL,
    StartDate DATE not null,
    EndDate DATE not null,
    HoursBooked INTEGER[][],
    HourlyRate INT not null
);

CREATE TABLE IF NOT EXISTS bids(
    BidID SERIAL PRIMARY KEY,
    BidderName varchar(40) NOT NULL,
    WorkerName varchar(40) NOT NULL,
    StartDate DATE not null,
    EndDate DATE not null,
    HoursBooked INTEGER[][],
    HourlyRate INT not null
);

CREATE TABLE IF NOT EXISTS availability(
    AvailabilityID SERIAL PRIMARY KEY,
    WorkerName VARCHAR(40) UNIQUE NOT NULL,
    AvailableHours INTEGER[][]
);
