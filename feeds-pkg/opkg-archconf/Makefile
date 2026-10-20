# opkg-archconf：补运行时 opkg 的架构声明（/etc/opkg/10-arch.conf）。
# 背景：istoreos-24.10 的 /etc/opkg.conf 里没有 arch 行，导致运行时
# opkg 装任何官方源包都报 "incompatible with the architectures configured"
#（2026-10-18 容器真机验证抓到，公版 la3 同病）。PKGARCH=all，无编译。
include $(TOPDIR)/rules.mk

PKG_NAME:=opkg-archconf
PKG_VERSION:=1.0
PKG_RELEASE:=1

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=base
	CATEGORY:=Base system
	TITLE:=opkg arch declarations for loongarch64 runtime
	PKGARCH:=all
endef

define Package/$(PKG_NAME)/description
	/etc/opkg/10-arch.conf：arch all + arch loongarch64_generic，
	让运行时 opkg 能装官方 24.10 loongarch64_generic 源。
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/etc/opkg
	$(INSTALL_DATA) ./files/10-arch.conf $(1)/etc/opkg/10-arch.conf
endef

define Build/Compile
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
