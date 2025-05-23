local json = require ("dkjson")

-- expects the file name of the lua to be converted without the .lua extension
local fname = arg[1]

-- local tbl = require (fname)
local tbl = dofile(fname .. '.lua')

local str = json.encode (tbl, { indent = true })

local f = io.open(fname .. '.json', 'w')
f:write(str)
f:close()