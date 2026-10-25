'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const sharp = require('sharp');

function makeBase() {
  return sharp({
    create: {
      width: 256,
      height: 256,
      channels: 3,
      background: { r: 200, g: 100, b: 50 }
    }
  });
}

async function main() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sharp-test-'));
  const inJpg = path.join(dir, 'in.jpg');
  const inPng = path.join(dir, 'in.png');
  const inWebp = path.join(dir, 'in.webp');

  console.log('sharp.versions =', JSON.stringify(sharp.versions, null, 2));

  // Build a 256x256 source image and encode it as JPEG, PNG and WebP.
  fs.writeFileSync(inJpg, await makeBase().jpeg().toBuffer());
  fs.writeFileSync(inPng, await makeBase().png().toBuffer());
  fs.writeFileSync(inWebp, await makeBase().webp().toBuffer());

  // resize(128,128) -> WebP buffer
  const resized = await sharp(inPng).resize(128, 128).webp().toBuffer();
  if (!(resized.length > 0)) throw new Error('resized WebP buffer is empty');

  // sharp('in.jpg') -> jpeg / png / webp
  const outJpeg = await sharp(inJpg).jpeg().toBuffer();
  const outPng = await sharp(inJpg).png().toBuffer();
  const outWebp = await sharp(inJpg).webp().toBuffer();

  const meta = await sharp(inJpg).metadata();

  console.log('resize(128,128).webp() bytes =', resized.length);
  console.log('sharp(in.jpg).jpeg() bytes    =', outJpeg.length);
  console.log('sharp(in.jpg).png() bytes     =', outPng.length);
  console.log('sharp(in.jpg).webp() bytes    =', outWebp.length);
  console.log('in.jpg metadata =', JSON.stringify({
    format: meta.format,
    width: meta.width,
    height: meta.height,
    channels: meta.channels
  }));

  const libvipsOk = sharp.versions.vips === '8.18.7';
  const sizesOk = [resized, outJpeg, outPng, outWebp].every((b) => b.length > 0);
  const metaOk = meta.format === 'jpeg' && meta.width === 256 && meta.height === 256;

  if (!libvipsOk || !sizesOk || !metaOk) {
    console.error('TEST FAIL', { libvipsOk, sizesOk, metaOk });
    process.exit(1);
  }
  console.log('TEST PASS');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
