create table if not exists entries (
    user_id string primary key,
    elapsed_time float not null
);

create table if not exists error_logs (
    user_id string not null,
    error_log string not null
);
