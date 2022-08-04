from .shader import ULFilter
from mathutils import Vector


glsl = """
uniform sampler2D bgl_RenderedTexture;
in vec4 bgl_TexCoord;
vec2 texcoord = bgl_TexCoord.xy;
uniform vec3 color;


vec4 gradient(vec4 coo)
{
	vec4 stripes = coo;
	stripes.r *= color.x;
	stripes.g *= color.y;
	stripes.b *= color.z;
	stripes.a = 1.0;
	return stripes;
}

void main (void) 
{ 		
	vec4 value = texture(bgl_RenderedTexture, texcoord);
		

// 	gl_FragColor = gradient(vec4(clamp(gl_TexCoord[3].s,0.0,1.0)));
	gl_FragColor.rgb = gradient(value).rgb;
	gl_FragColor.a = 1.0;	
}
"""

class Levels(ULFilter):

    def __init__(self, color=(1., 1., 1.), idx: int = None) -> None:
        self.settings = {'color': Vector(color)}
        super().__init__(glsl, idx, {'color': self.settings})