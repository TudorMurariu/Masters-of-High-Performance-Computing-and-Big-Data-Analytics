-- Load the CSV file with 4 fields: title, author, year, tags
books = LOAD 'books.csv' USING PigStorage(',') 
        AS (title:chararray, author:chararray, year:int, tag1:chararray, tag2:chararray);


-- Filter books related to Hadoop
hadoop_books = FILTER books BY tag1 MATCHES '.*hadoop.*' OR tag2 MATCHES '.*hadoop.*';

-- Group the books by publication year
grouped_by_year = GROUP hadoop_books BY year;

-- Count number of hadoop books published each year
books_per_year = FOREACH grouped_by_year GENERATE group AS year, COUNT(hadoop_books) AS count;

-- Display the result
DUMP books_per_year;