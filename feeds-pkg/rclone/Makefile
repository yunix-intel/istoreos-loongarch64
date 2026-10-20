# rclone (Go) for loongarch64 — binary repack, tool only (no daemon)
include $(TOPDIR)/rules.mk

PKG_NAME:=rclone
PKG_VERSION:=1.75.2
PKG_RELEASE:=1

PKG_SOURCE:=rclone-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/rclone
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Cloud sync tool (Go)
  URL:=https://github.com/rclone/rclone
endef

define Package/rclone/description
  rclone 龙芯版：宿主 Go GOARCH=loong64 直编，112M 属正常。
  命令行工具，无守护进程：rclone config 配网盘后用。
endef

define Package/rclone/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BINDIR)/rclone $(1)/usr/bin/
endef

define Build/Compile
endef

$(eval $(call BuildPackage,rclone))
