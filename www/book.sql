create table books (
    `id` varchar(50) not null,
    `name` varchar(50) not null,
    `author` varchar(200) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;