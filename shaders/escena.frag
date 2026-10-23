#version 300 es
// escena.frag - Sombreado PBR de la escena (GLSL ES 3.00 / WebGL 2).

precision mediump float;

in vec3 vPosMundo;
in vec3 vNormal;
in vec2 vUV;
in vec4 vTinte;
in vec4 vColor;

uniform sampler2D p3d_Texture0;

uniform struct {
    vec4 baseColor;
    vec4 diffuse;
    vec4 emission;
    float roughness;
    float metallic;
} p3d_Material;

uniform vec4 uColor;
uniform vec3 uEmision;
uniform int uModoAlfa;       // 0 = opaco, 1 = recorte, 2 = translucido
uniform float uCorte;

uniform float uMetalico;
uniform float uRugosidad;
uniform float uCapa;
uniform float uRugosidadCapa;

uniform vec3 uDirLuz;
uniform vec3 uColorLuz;
uniform vec3 uAmbienteCielo;
uniform vec3 uAmbienteSuelo;
uniform vec3 uPosCamara;
uniform vec3 uColorNiebla;
uniform float uDensidadNiebla;

uniform vec3 uLuzEntradaPos;
uniform vec3 uLuzEntradaColor;

out vec4 FragColor;

const float PI = 3.14159265359;

vec3 fresnel(float coseno, vec3 f0) {
    float t = 1.0 - clamp(coseno, 0.0, 1.0);
    return f0 + (1.0 - f0) * pow(t, 5.0);
}

vec3 especular(vec3 N, vec3 V, vec3 L, vec3 f0, float rugosidad) {
    float nv = max(dot(N, V), 0.0001);
    float nl = max(dot(N, L), 0.0);
    if (nl <= 0.0 || dot(V + L, V + L) < 0.000001) {
        return vec3(0.0);
    }
    vec3 H = normalize(V + L);
    float nh = max(dot(N, H), 0.0);
    float a = max(rugosidad * rugosidad, 0.0025);
    float a2 = a * a;
    float denominador = nh * nh * (a2 - 1.0) + 1.0;
    float D = a2 / max(PI * denominador * denominador, 0.00000001);
    float gv = 2.0 * nv / (nv + sqrt(a2 + (1.0 - a2) * nv * nv));
    float gl = 2.0 * nl / (nl + sqrt(a2 + (1.0 - a2) * nl * nl));
    return D * gv * gl * fresnel(dot(V, H), f0) / max(4.0 * nv * nl, 0.0001);
}

void main() {
    vec4 matCol = p3d_Material.baseColor;
    if (matCol.a <= 0.001) {
        matCol = vec4(1.0);
    }

    vec4 texCol = texture(p3d_Texture0, vUV);
    vec4 base = matCol * texCol * uColor * vTinte * vColor;

    if (uModoAlfa == 1 && base.a < uCorte) {
        discard;
    }

    vec3 N = normalize(vNormal);
    if (!gl_FrontFacing) {
        N = -N;
    }

    vec3 V = normalize(uPosCamara - vPosMundo);
    vec3 L = normalize(uDirLuz);

    float nv = max(dot(N, V), 0.0);
    float nl = max(dot(N, L), 0.0);

    float metal = clamp(max(uMetalico, p3d_Material.metallic), 0.0, 1.0);
    float rug = clamp(p3d_Material.roughness > 0.0 ? p3d_Material.roughness : uRugosidad, 0.05, 1.0);

    vec3 f0 = mix(vec3(0.04), base.rgb, metal);
    vec3 F = fresnel(nv, f0);

    // Iluminacion ambiental hemisferica
    vec3 ambiente = mix(uAmbienteSuelo, uAmbienteCielo, clamp(N.y * 0.5 + 0.5, 0.0, 1.0));

    // Luz solar directa
    vec3 color = base.rgb * (1.0 - metal) * (1.0 - F) * (ambiente + uColorLuz * nl);
    color += PI * especular(N, V, L, f0, rug) * uColorLuz * nl;

    // Luz puntual calida en la portada / entrada del panteon
    vec3 L_ent = uLuzEntradaPos - vPosMundo;
    float dist_ent = length(L_ent);
    if (dist_ent < 35.0) {
        vec3 l_dir = L_ent / max(dist_ent, 0.001);
        float nl_ent = max(dot(N, l_dir), 0.0);
        float aten = 1.0 / (1.0 + 0.12 * dist_ent + 0.02 * dist_ent * dist_ent);
        vec3 col_ent = uLuzEntradaColor * aten;
        color += base.rgb * (1.0 - metal) * (1.0 - F) * col_ent * nl_ent;
        color += PI * especular(N, V, l_dir, f0, rug) * col_ent * nl_ent;
    }

    // Emision (de material o uniforme)
    vec3 emision = uEmision + p3d_Material.emission.rgb;
    color += emision;

    // Niebla por distancia
    float distancia = length(vPosMundo - uPosCamara);
    float niebla = 1.0 - exp(-pow(uDensidadNiebla * distancia, 1.5));
    color = mix(color, uColorNiebla, clamp(niebla, 0.0, 1.0));

    // Correccion gamma 2.2
    color = pow(max(color, vec3(0.0)), vec3(1.0 / 2.2));

    FragColor = vec4(color, uModoAlfa == 2 ? base.a : 1.0);
}
