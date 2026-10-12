# filebrowser (Go) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=filebrowser
PKG_VERSION:=2.63.23
PKG_RELEASE:=1

PKG_SOURCE:=filebrowser-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/filebrowser
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Web file manager (Go)
  URL:=https://github.com/filebrowser/filebrowser
endef

define Package/filebrowser/description
  filebrowser 龙芯版：宿主 Go GOARCH=loong64 直编，静态链接。
  默认根目录 /srv，数据库 /etc/filebrowser.db，首次跑自动初始化管理员。
endef

define Package/filebrowser/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/srv
	$(INSTALL_BIN) $(PKG_BINDIR)/filebrowser $(1)/usr/bin/
	$(INSTALL_BIN) ./files/filebrowser.init $(1)/etc/init.d/filebrowser
endef

define Build/Compile
endef

$(eval $(call BuildPackage,filebrowser))
