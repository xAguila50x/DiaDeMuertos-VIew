#version 300 es
// escena.vert - Vertices de la escena (GLSL ES 3.00).

precision mediump float;

in vec3 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;

uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform vec2 uEscalaUV;
uniform vec4 uTinte;

out vec3 vPosMundo;
out vec3 vNormal;
out vec2 vUV;
out vec4 vTinte;
out vec4 vColor;

void main() {
    vPosMundo = (p3d_ModelMatrix * vec4(p3d_Vertex, 1.0)).xyz;
    vNormal = p3d_NormalMatrix * p3d_Normal;
    vTinte = uTinte;
    vColor = p3d_Color;
    vUV = p3d_MultiTexCoord0 * uEscalaUV;
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(p3d_Vertex, 1.0);
}
