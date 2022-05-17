''' Add this to your menu.py '''
import nuke

# Higx Tools
toolbar = nuke.toolbar("Nodes")
m = toolbar.addMenu("Higx Tools", icon="higx_tools.png")
m_general = m.addMenu("General", icon="h_pointRender.png")
m_generator = m.addMenu("Generator", icon="h_pointGenerator.png")
m_modifier = m.addMenu("Modifier", icon="h_pointModifier.png")
m_shader = m.addMenu("Shader", icon="h_pointShader.png")

# General
m_general.addCommand("Point_Render", "nuke.createNode('Point_Render')", icon="h_pointRender.png")
m_general.addCommand("Point_3DPreview", "nuke.createNode('Point_3DPreview')", icon="h_pointRender.png")

# Generators
m_generator.addCommand("Point_Plane", "nuke.createNode('Point_Plane')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_Sphere", "nuke.createNode('Point_Sphere')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_Torus", "nuke.createNode('Point_Torus')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_Cylinder", "nuke.createNode('Point_Cylinder')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_Polygon", "nuke.createNode('Point_Polygon')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_UnitSphere_NU", "nuke.createNode('Point_UnitSphere')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_UnitCube_NU", "nuke.createNode('Point_UnitCube')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_Grid_NU", "nuke.createNode('Point_Grid')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_Particles_NU", "nuke.createNode('Point_Particles')", icon="h_pointGenerator.png")
# m_generator.addCommand("Point_Lightning_NU", "nuke.createNode('Point_Lightning')", icon="h_pointGenerator.png") ##comming soon
m_generator.addCommand("Point_GeoSource_NU", "nuke.createNode('Point_GeoSource')", icon="h_pointGenerator.png")
m_generator.addCommand("Point_GeoSourceUV_NU", "nuke.createNode('Point_GeoSourceUV')", icon="h_pointGenerator.png")

# Modifiers
m_modifier.addCommand("Point_Expression", "nuke.createNode('Point_Expression')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_Fractal", "nuke.createNode('Point_Fractal')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_Fractal_Evolve", "nuke.createNode('Point_Fractal_Evolve')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_RadialForce", "nuke.createNode('Point_RadialForce')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_Transform", "nuke.createNode('Point_Transform')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_Twist", "nuke.createNode('Point_Twist')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_Merge_NU", "nuke.createNode('Point_Merge_NU')", icon="h_pointModifier.png")
m_modifier.addCommand("Point_Dublicator_NU", "nuke.createNode('Point_Dublicator_NU')", icon="h_pointModifier.png")
# m_modifier.addCommand("Point_Weave_NU", "nuke.createNode('Point_Weave')", icon="h_pointModifier.png") ##comming soon

# Textures
m_shader.addCommand("Point_Distance", "nuke.createNode('Point_Distance')", icon="h_pointShader.png")
m_shader.addCommand("Point_FractalMask", "nuke.createNode('Point_FractalMask')", icon="h_pointShader.png")
m_shader.addCommand("Point_FractalTexture", "nuke.createNode('Point_FractalTexture')", icon="h_pointShader.png")
m_shader.addCommand("Point_Light", "nuke.createNode('Point_Light')", icon="h_pointShader.png")
m_shader.addCommand("Point_MotionShader", "nuke.createNode('Point_MotionShader')", icon="h_pointShader.png")
m_shader.addCommand("Point_Normal", "nuke.createNode('Point_Normal')", icon="h_pointShader.png")
m_shader.addCommand("Point_Proximity", "nuke.createNode('Point_Proximity')", icon="h_pointShader.png")
m_shader.addCommand("Point_ReflectionShader", "nuke.createNode('Point_ReflectionShader')", icon="h_pointShader.png")
m_shader.addCommand("Point_Texture", "nuke.createNode('Point_Texture')", icon="h_pointShader.png")
m_shader.addCommand("Point_VectorMathOps", "nuke.createNode('Point_Vector_Math_Ops')", icon="h_pointShader.png")
