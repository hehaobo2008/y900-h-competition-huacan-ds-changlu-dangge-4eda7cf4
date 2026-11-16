import * as THREE from 'three';
import {loadAssetURL} from './asset_transport.js';

const textures=[];
// Keep TextureLoader's immediate return value. Each image loads independently
// so models can parse while other images and models are still arriving.
export class AssetTextureLoader extends THREE.TextureLoader{
  load(path,onLoad,onProgress,onError){
    const texture=new THREE.Texture();
    const ready=loadAssetURL(path).then(url=>new Promise((resolve,reject)=>{
      new THREE.ImageLoader(this.manager).setCrossOrigin(this.crossOrigin).load(url,image=>{
        texture.image=image;texture.needsUpdate=true;resolve(texture);
      },onProgress,reject);
    }));
    textures.push(ready.then(()=>null,error=>error));
    ready.then(value=>onLoad?.(value),error=>onError?.(error));
    return texture;
  }
}
export async function waitForAssetTextures(){
  const errors=await Promise.all(textures);const error=errors.find(Boolean);if(error)throw error;
}
