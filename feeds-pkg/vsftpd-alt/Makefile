# vsftpd-alt (C) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=vsftpd-alt
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_SOURCE:=vsftpd-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/vsftpd-alt
  SECTION:=net
  CATEGORY:=Network
  TITLE:=FTP server (C)
endef

define Package/vsftpd-alt/description
  vsftpd-alt 龙芯版：交叉工具链编，musl 动态链接。配置 /etc/vsftpd.conf。
endef

define Package/vsftpd-alt/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/vsftpd $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/vsftpd.init $(1)/etc/init.d/vsftpd-alt
endef

define Build/Compile
endef

$(eval $(call BuildPackage,vsftpd-alt))
