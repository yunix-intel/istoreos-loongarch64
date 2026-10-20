# luci-lib-docker v0.3.4（lisaac）：dockerman 的 Lua 引擎库，单文件。
# 去掉上游 @(aarch64||arm||x86_64) 架构锁（纯 Lua，loong64 照跑）。
include $(TOPDIR)/rules.mk

PKG_NAME:=luci-lib-docker
PKG_VERSION:=0.3.4
PKG_RELEASE:=1

PKG_MAINTAINER:=lisaac <lisaac.cn@gmail.com>

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=luci
	CATEGORY:=LuCI
	SUBMENU:=Libraries
	TITLE:=LuCI library for docker
	DEPENDS:=+luci-lib-jsonc
	PKGARCH:=all
endef

define Package/$(PKG_NAME)/description
	Docker Engine API for LuCI (dockerman 依赖).
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/model
	$(INSTALL_DATA) ./files/docker.lua $(1)/usr/lib/lua/luci/model/docker.lua
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
