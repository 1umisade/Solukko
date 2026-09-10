// Solukon molekyylipopupin Babylon-paketti: vain ne osat, joita simulaatiot/kortti.html kayttaa.
// Rakennetaan esbuildilla (tyokalut/babylon_kortti_build.md kertoo miten). Tulos: simulaatiot/babylon-kortti.js
import { Engine } from "@babylonjs/core/Engines/engine";
import { Scene } from "@babylonjs/core/scene";
import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
import { Axis } from "@babylonjs/core/Maths/math.axis";
import { Color3, Color4 } from "@babylonjs/core/Maths/math.color";
import { Constants } from "@babylonjs/core/Engines/constants";
import { Effect } from "@babylonjs/core/Materials/effect";
import { Frustum } from "@babylonjs/core/Maths/math.frustum";
import { Matrix, Vector3, Quaternion } from "@babylonjs/core/Maths/math.vector";
import { Viewport } from "@babylonjs/core/Maths/math.viewport";
import { CreateLineSystem } from "@babylonjs/core/Meshes/Builders/linesBuilder";
import { CreatePlane } from "@babylonjs/core/Meshes/Builders/planeBuilder";
import { CreateSphere } from "@babylonjs/core/Meshes/Builders/sphereBuilder";
import { RenderTargetTexture } from "@babylonjs/core/Materials/Textures/renderTargetTexture";
import { ShaderMaterial } from "@babylonjs/core/Materials/shaderMaterial";
// side effects the editor code relies on
import "@babylonjs/core/Meshes/thinInstanceMesh";          // mesh.thinInstanceSetBuffer
import "@babylonjs/core/Culling/ray";                       // scene.createPickingRay
import "@babylonjs/core/Animations/animatable";             // scene.stopAnimation
import "@babylonjs/core/Engines/Extensions/engine.alpha";
import "@babylonjs/core/Engines/Extensions/engine.dynamicBuffer";
import "@babylonjs/core/Engines/Extensions/engine.renderTarget";
import "@babylonjs/core/Engines/Extensions/engine.rawTexture";
import "@babylonjs/core/Engines/Extensions/engine.readTexture";

window.BABYLON = { Engine, Scene, ArcRotateCamera, Axis, Color3, Color4, Constants, Effect, Frustum, Matrix, Vector3, Quaternion, Viewport,
  MeshBuilder: { CreateLineSystem, CreatePlane, CreateSphere }, RenderTargetTexture, ShaderMaterial };
