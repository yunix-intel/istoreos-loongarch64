# luci-app-dockerman v0.5.26（lisaac）：Docker 管理页，纯 Lua+静态资源。
# 去掉上游 @(aarch64||arm||x86_64) 架构锁；依赖精简（不要 dockerd——
# 我们连宿主 daemon 的 socket；init.d 不装；uhttpd 超时等由装机脚本处理）。
# 中文：po/zh-cn → i18n/dockerman.zh-cn.lmo（po2lmo 宿主工具）。
include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-dockerman
PKG_VERSION:=0.5.26
PKG_RELEASE:=1

PKG_MAINTAINER:=lisaac <lisaac.cn@gmail.com>

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=luci
	CATEGORY:=LuCI
	SUBMENU:=Applications
	TITLE:=LuCI Support for docker
	DEPENDS:=+luci-compat +luci-lib-docker +luci-lib-ip
	# 注：运行时另需 docker CLI 与 ttyd（二进制，官方源有 loong64 版，
	# 容器里已装）；刻意不写进 DEPENDS——docker 的依赖树会拖进无
	# loongarch 支持的 libseccomp（feed 版），见 BUILDLOG。
	PKGARCH:=all
endef

define Package/$(PKG_NAME)/description
	Docker 管理页（容器/镜像/网络/卷）。连宿主 daemon 时把
	dockerd.dockerman.socket_path 指到挂载的 socket（如 /root/docker.sock）。
endef

define Build/Compile
	$(STAGING_DIR_HOST)/bin/po2lmo ./files/po/zh-cn/dockerman.po \
		$(PKG_BUILD_DIR)/dockerman.zh-cn.lmo
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/controller \
		$(1)/usr/lib/lua/luci/model/cbi/dockerman \
		$(1)/usr/lib/lua/luci/view/dockerman \
		$(1)/usr/lib/lua/luci/i18n $(1)/www \
		$(1)/etc/uci-defaults $(1)/usr/share/rpcd/acl.d
	$(INSTALL_DATA) ./files/luasrc/controller/dockerman.lua \
		$(1)/usr/lib/lua/luci/controller/
	$(INSTALL_DATA) ./files/luasrc/model/cbi/dockerman/*.lua \
		$(1)/usr/lib/lua/luci/model/cbi/dockerman/
	$(INSTALL_DATA) ./files/luasrc/view/dockerman/* \
		$(1)/usr/lib/lua/luci/view/dockerman/
	$(CP) ./files/htdocs/* $(1)/www/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/dockerman.zh-cn.lmo \
		$(1)/usr/lib/lua/luci/i18n/
	$(INSTALL_BIN) ./files/root/etc/uci-defaults/luci-app-dockerman \
		$(1)/etc/uci-defaults/
	$(INSTALL_DATA) ./files/root/usr/share/rpcd/acl.d/*.json \
		$(1)/usr/share/rpcd/acl.d/
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
