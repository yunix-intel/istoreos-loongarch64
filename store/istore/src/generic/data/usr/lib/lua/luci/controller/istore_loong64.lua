-- LuCI controller for the generic LoongArch64 iStore installer.
module("luci.controller.istore_loong64", package.seeall)

local http = require "luci.http"
local sys = require "luci.sys"
local uci = require "luci.model.uci"

function index()
	entry({"admin", "services", "istore-loong64"},
		template("istore_loong64/apps"), _("Loong64 Apps"), 60).dependent = false
	entry({"admin", "services", "istore-loong64", "app"},
		template("istore_loong64/app"), nil).dependent = false
	entry({"admin", "services", "istore-loong64", "action"},
		call("action")).dependent = false
end

local function valid_id(id)
	return id and id:match("^[a-z0-9_%-]+$") ~= nil
end

local function clean(v)
	if not v then return "" end
	return (v:gsub("[\r\n]", " "))
end

function action()
	local id = clean(http.formvalue("app"))
	local act = clean(http.formvalue("action"))
	local allowed = {
		install = true, upgrade = true, rm = true,
		start = true, stop = true, restart = true,
		status = true, ports = true, port = true, logs = true
	}

	if not valid_id(id) then
		http.redirect(luci.dispatcher.build_url("admin/services/istore-loong64"))
		return
	end

	if act == "save" then
		local c = uci.cursor()
		if not c:get(id, "main") then
			c:section(id, "main", "main")
		end
		c:set(id, "main", "variant", clean(http.formvalue("variant")) or "public")
		c:set(id, "main", "image", clean(http.formvalue("image")))
		c:set(id, "main", "host_port", clean(http.formvalue("host_port")))
		c:set(id, "main", "data_path", clean(http.formvalue("data_path")))
		c:set(id, "main", "env_file", clean(http.formvalue("env_file")))
		c:commit(id)
		http.redirect(luci.dispatcher.build_url("admin/services/istore-loong64/app")
			.. "?app=" .. id .. "&msg=" .. http.urlencode("saved"))
		return
	end

	if not allowed[act] then act = "status" end

	local out
	if act == "install" or act == "upgrade" then
		local logf = "/tmp/istore-" .. id .. ".log"
		os.execute(": > " .. logf .. "; /usr/libexec/istorec/loong64.sh "
			.. id .. " " .. act .. " >>" .. logf .. " 2>&1 &")
		out = "started in background; log: " .. logf
	elseif act == "logs" then
		out = sys.exec("/usr/libexec/istorec/loong64.sh " .. id .. " logs 200 2>&1")
	else
		out = sys.exec("/usr/libexec/istorec/loong64.sh " .. id .. " " .. act .. " 2>&1")
	end

	local f = io.open("/tmp/istore-" .. id .. ".last", "w")
	if f then
		f:write(out or "")
		f:close()
	end
	http.redirect(luci.dispatcher.build_url("admin/services/istore-loong64/app")
		.. "?app=" .. id .. "&msg=" .. http.urlencode(act))
end
