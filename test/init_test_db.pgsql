
create table mf_mod_lut(
    mf_mod_lut_id smallserial primary key,
    mod_bit integer not null,
    mod_text text
);

insert into mf_mod_lut (mod_bit, mod_text) values 
    (2^0, 'Regenerate 0.6 Mana per Second per 10 Devotion'),
    (2^1, '3% increased Effect of non-Damaging Ailments on Enemies per 10 Devotion'),
    (2^2, '4% increased Area Damage per 10 Devotion'),
    (2^3, '1% increased effect of Non-Curse Auras per 10 Devotion'),
    (2^4, '4% increased Brand Damage per 10 Devotion'),
    (2^5, 'Channelling Skills deal 4% increased Damage per 10 Devotion'),
    (2^6, '4% reduced Duration of Curses on you per 10 Devotion'),
    (2^7, '4% reduced Elemental Ailment Duration on you per 10 Devotion'),
    (2^8, '4% increased Elemental Damage per 10 Devotion'),
    (2^9, '+2% to all Elemental Resistances per 10 Devotion'),
    (2^10, 'Minions have +60 to Accuracy Rating per 10 Devotion'),
    (2^11, '1% increased Minion Attack and Cast Speed per 10 Devotion'),
    (2^12, '1% reduced Mana Cost of Skills per 10 Devotion'),
    (2^13, '3% increased Defences from Equipped Shield per 10 Devotion'),
    (2^14, '4% increased Totem Damage per 10 Devotion');

create table class_lut(
    class_id smallserial primary key,
    base_class_name text,
    ascendancy_class_name text
);

insert into class_lut (base_class_name, ascendancy_class_name) values
    ('Witch', 'Elementalist'),
    ('Witch', 'Necromancer'),
    ('Witch', 'Occultist'),
    ('Shadow', 'Trickster'),
    ('Shadow', 'Assassin'),
    ('Shadow', 'Saboteur'),
    ('Ranger', 'Deadeye'),
    ('Ranger', 'Pathfinder'),
    ('Ranger', 'Warden'),
    ('Ranger', 'Raider'),
    ('Duelist', 'Champion'),
    ('Duelist', 'Slayer'),
    ('Duelist', 'Gladiator'),
    ('Marauder', 'Chieftain'),
    ('Marauder', 'Juggernaut'),
    ('Marauder', 'Berserker'),
    ('Templar', 'Inquisitor'),
    ('Templar', 'Guardian'),
    ('Templar', 'Hierophant'),
    ('Scion', 'Ascendant');

create table jewel_type_lut(
    jewel_type_id smallserial primary key,
    type_name text
);

insert into jewel_type_lut (type_name) values 
    ('Militant Faith'), 
    ('Brutal Restraint'),
    ('Lethal Pride'),
    ('Elegant Hubris'),
    ('Glorious Vanity');

create table general_lut(
    general_id smallserial primary key,
    general_name text
);

insert into general_lut (general_name) values
    ('Asenath'),
    ('Balbala'), 
    ('Nasima'), 
    ('Cadiro'), 
    ('Caspiro'), 
    ('Victario'), 
    ('Ahuana'), 
    ('Doryani'), 
    ('Xibaqua'), 
    ('Akoya'), 
    ('Kaom'), 
    ('Rakiata'), 
    ('Avarius'), 
    ('Dominus'), 
    ('Maxarius');

create table league(
    league_id smallserial primary key,
    league_name text constraint uk_league_name unique not null,
    hardcore boolean default false,
    league_start timestamp with time zone,
    league_end timestamp with time zone
);


create table character(
    character_id bigserial primary key,
    league_id smallserial references league(league_id),
    ggg_id text not null constraint uk_character_ggg_id unique,
    character_name text not null,
    class_id smallserial references class_lut(class_id),
    character_level integer not null,
    account_name text not null,
    ladder_rank integer not null,
    delve_depth integer,
    last_scan timestamp with time zone
);

-- think i'm gonna declare that there can only be ONE character of each class with the same name

create table jewel(
    jewel_id bigserial primary key,
    character_id bigserial references character(character_id),
    jewel_type_id smallserial references jewel_type_lut(jewel_type_id),
    seed integer not null,
    general_id smallserial references general_lut(general_id),
    mf_mods integer null,
    socket_id integer not null,
    drawing json not null,
    scan_date timestamp with time zone
);

create table socket_lut(
    socket_id integer primary key,
    node_id integer not null,
    pob_name text not null,
    description text not null
);

insert into socket_lut (socket_id, node_id, pob_name, description) values
(0, 26725, 'Marauder', '')
(1, 36634, 'Mind Over Matter', 'Templar/Witch Mid-tree'),
(2, 33989, 'Supreme Ego', 'Shadow/Ranger Mid-tree'),
(3, 41263, 'Pain Attunement', 'Witch/Shadow Mid-tree'),
(4, 60735, 'Wind Dancer', 'Ranger'),
(5, 61834, 'Ghost Dance', 'Shadow'),
(6, 31683, 'Iron Grip', 'Scion S'),
(7, 28475, 'Unwavering Stance', 'Duelist/Marauder Mid-tree'),
(8, 6230, 'Iron Will', 'Scion NW'),
(9, 48768, 'Conduit', 'Scion NE'),
(10, 34483, 'Elemental Equilibrium', 'Ranger/Duelist Mid-tree'),
(11, 7960, 'Templar/Witch', 'Elemental Damage Cluster Socket'),
(12, 46882, 'Point Blank', 'Evasion Cluster Socket'),
(13, 55190, 'Resolute Technique', 'Armour Cluster Socket'),
(14, 61419, 'Minion Instability', 'Witch'),
(15, 2491, 'Arsenal of Vengeance', 'Melee Damage Cluster Socket'),
(16, 54127, 'Duelist', ''),
(17, 32763, 'Perfect Agony', 'Projectile Damage Cluster Socket'),
(18, 26196, 'The Agnostic', 'Templar'),
(19, 33631, 'Eternal Youth', 'Marauder/Templar Mid-tree'),
(20, 21984, 'Eldritch Battery', 'Mana Cluster Socket');


-- the machines have won, it's over
CREATE OR REPLACE FUNCTION get_mod_texts(sum_val integer)
RETURNS TABLE(
    bit1 integer,
    text1 text,
    bit2 integer,
    text2 text
)
LANGUAGE plpgsql
AS $$
DECLARE
    i integer;
    current_bit integer;
BEGIN
    FOR i IN 0..14 LOOP
        current_bit := (1 << i);
        IF (sum_val & current_bit) != 0 THEN
            IF bit1 IS NULL THEN
                SELECT mod_bit, mod_text INTO bit1, text1
                FROM mf_mod_lut
                WHERE mod_bit = current_bit;
            ELSE
                SELECT mod_bit, mod_text INTO bit2, text2
                FROM mf_mod_lut
                WHERE mod_bit = current_bit;
                RETURN NEXT;
                RETURN;
            END IF;
        END IF;
    END LOOP;

    RETURN;
END;
$$;


CREATE OR REPLACE FUNCTION get_mod_text_by_idx(sum_val integer, idx integer)
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    i integer;
    current_bit integer;
    found_count integer := 0;
    mod_text_result text;
BEGIN
    IF idx NOT IN (1, 2) THEN
        RAISE EXCEPTION 'idx must be 1 or 2';
    END IF;

    FOR i IN 0..14 LOOP
        current_bit := (1 << i);
        IF (sum_val & current_bit) != 0 THEN
            found_count := found_count + 1;
            IF found_count = idx THEN
                SELECT mod_text INTO mod_text_result
                FROM mf_mod_lut
                WHERE mod_bit = current_bit;
                RETURN mod_text_result;
            END IF;
        END IF;
    END LOOP;

    -- If we didn't find enough set bits
    RETURN NULL;
END;
$$;


CREATE OR REPLACE FUNCTION mf_mods_contains_bit(
    mf_mods INTEGER,
    mod_bit INTEGER
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    power INTEGER := 1;
BEGIN
    IF mod_bit <= 0 OR (mod_bit & (mod_bit - 1)) <> 0 THEN
        -- mod_bit must be a power of 2
        RAISE EXCEPTION 'mod_bit must be a power of 2';
    END IF;

    WHILE power <= mf_mods LOOP
        IF power <> mod_bit AND mf_mods = mod_bit + power THEN
            RETURN TRUE;
        END IF;
        power := power * 2;
    END LOOP;

    RETURN FALSE;
END;
$$;







-- league
--     - lists each league along with its start and end

-- character
--     - represents a character in a league
--     - lists things like last time scanned, ladder rank etc

-- jewel
--     - base, seed, general
--     - MF mods will be joined with a separate table
--     - socket that it was equipped in
--     - timestamp equipped
    
-- jewel_mf_mods
--     - jewel_id, mf_mod
--     - every militant faith jewel will have exactly 2 entries in this table

-- mf_mod_lut
--     - just lists the militant faith mods


-- query practice

-- here's my jewel, give me a list of all jewels of the same seed that were equipped, and their characters

-- ** huge disclaimer on the MF example, this generates 2 rows for each jewel so you need to 'transpose' the mf mods (or something)

-- select j.base, j.seed, j.general, mml.mod from jewel j
-- join character c on c.character_id = j.character_id
-- left join jewel_mf_mods on jmm.jewel_id = j.jewel_id
-- join mf_mod_lut mml on jmm.mf_mod_id on mml.mf_mod_id
-- where j.base = 'Militant Faith'
-- and j.seed = '12345'


-- ok scratch all that, we are just gonna use a bit string????

-- doesn't exactly fix all our problems, but here's a couple scenarios:

-- exact match on the mods is the same as the bit strings match
-- using & will yield some results:
--     & result is 0 -> 0 matches
--     & result > 0 -> 1 match


-- there are currently 15 mf mods, so this can easily be represented by integer type
-- we can build the query with the 'bits' in mind, so it's no problem to split it into 2 separate joins against mf_mod_lut
