from rlutilities.linear_algebra import vec3, mat3

def three_vec3_to_mat3(f: vec3, l: vec3, u: vec3) -> mat3:
    return mat3(f[0], l[0], u[0],
                f[1], l[1], u[1],
                f[2], l[2], u[2])

def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)