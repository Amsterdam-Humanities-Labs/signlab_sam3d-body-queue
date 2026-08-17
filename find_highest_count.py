import json
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import os

def find_highest_count_from_string(json_string):
    """
    Find the id with highest count for both l_hand and r_hand from JSON string.
    Also extract centroid data.
    
    Args:
        json_string (str): JSON data as string
        
    Returns:
        dict: Dictionary containing highest count ids and centroid for both hands
    """
    data = json.loads(json_string)
    
    result = {}
    
    # Find highest count for l_hand
    if 'l_hand' in data and data['l_hand']:
        max_l_hand = max(data['l_hand'], key=lambda x: x['count'])
        result['l_hand'] = {
            'id': max_l_hand['id'],
            'count': max_l_hand['count'],
            'centroid': max_l_hand.get('centroid', [])
        }
    
    # Find highest count for r_hand
    if 'r_hand' in data and data['r_hand']:
        max_r_hand = max(data['r_hand'], key=lambda x: x['count'])
        result['r_hand'] = {
            'id': max_r_hand['id'],
            'count': max_r_hand['count'],
            'centroid': max_r_hand.get('centroid', [])
        }
    
    return result

def find_top_n_counts_from_string(json_string, n=10):
    """
    Find the top N ids with highest count for both l_hand and r_hand from JSON string.
    Also extract centroid data and preserve all original fields.
    
    Args:
        json_string (str): JSON data as string
        n (int): Number of top entries to return
        
    Returns:
        dict: Dictionary containing top N count ids and all original data for both hands
    """
    data = json.loads(json_string)
    
    result = {}
    
    # Find top N for l_hand
    if 'l_hand' in data and data['l_hand']:
        sorted_l_hand = sorted(data['l_hand'], key=lambda x: x['count'], reverse=True)
        result['l_hand'] = []
        for item in sorted_l_hand[:n]:
            # Preserve all original fields
            cluster_data = {
                'id': item['id'],
                'count': item['count'],
                'centroid': item.get('centroid', []),
                'members': item.get('members', [])
            }
            result['l_hand'].append(cluster_data)
    
    # Find top N for r_hand
    if 'r_hand' in data and data['r_hand']:
        sorted_r_hand = sorted(data['r_hand'], key=lambda x: x['count'], reverse=True)
        result['r_hand'] = []
        for item in sorted_r_hand[:n]:
            # Preserve all original fields
            cluster_data = {
                'id': item['id'],
                'count': item['count'],
                'centroid': item.get('centroid', []),
                'members': item.get('members', [])
            }
            result['r_hand'].append(cluster_data)
    
    return result

def get_hand_connections():
    """
    Define hand keypoint connections for VitPose hand model (21 keypoints).
    """
    # Hand connections based on anatomical structure
    connections = [
        # Thumb
        (0, 1), (1, 2), (2, 3), (3, 4),
        # Index finger
        (0, 5), (5, 6), (6, 7), (7, 8),
        # Middle finger
        (0, 9), (9, 10), (10, 11), (11, 12),
        # Ring finger
        (0, 13), (13, 14), (14, 15), (15, 16),
        # Pinky
        (0, 17), (17, 18), (18, 19), (19, 20)
    ]
    return connections

def visualize_hand_keypoints(centroid, hand_type='hand', save_path=None):
    """
    Create 3D visualization of hand keypoints with connections.
    
    Args:
        centroid (list): List of 3D coordinates for hand keypoints
        hand_type (str): Type of hand ('l_hand' or 'r_hand')
        save_path (str): Path to save the PNG file
    """
    if not centroid or len(centroid) != 21:
        print(f"Invalid centroid data. Expected 21 keypoints, got {len(centroid) if centroid else 0}")
        return
    
    # Convert to numpy array
    keypoints = np.array(centroid)
    
    # Create 3D plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot keypoints
    ax.scatter(keypoints[:, 0], keypoints[:, 1], keypoints[:, 2], 
               c='red', s=50, alpha=0.8)
    
    # Add keypoint labels
    for i, (x, y, z) in enumerate(keypoints):
        ax.text(x, y, z, f'  {i}', fontsize=8)
    
    # Draw connections
    connections = get_hand_connections()
    for start, end in connections:
        start_point = keypoints[start]
        end_point = keypoints[end]
        ax.plot([start_point[0], end_point[0]], 
                [start_point[1], end_point[1]], 
                [start_point[2], end_point[2]], 
                'b-', linewidth=2, alpha=0.7)
    
    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'{hand_type.capitalize()} Keypoints (VitPose Model)')
    
    # Set equal aspect ratio
    max_range = np.array([keypoints[:, 0].max() - keypoints[:, 0].min(),
                         keypoints[:, 1].max() - keypoints[:, 1].min(),
                         keypoints[:, 2].max() - keypoints[:, 2].min()]).max() / 2.0
    mid_x = (keypoints[:, 0].max() + keypoints[:, 0].min()) * 0.5
    mid_y = (keypoints[:, 1].max() + keypoints[:, 1].min()) * 0.5
    mid_z = (keypoints[:, 2].max() + keypoints[:, 2].min()) * 0.5
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    
    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Hand visualization saved to {save_path}")
    else:
        plt.show()
    
    plt.close()

# Hand keypoint indices for each finger (from cluster.py)
FINGER_INDICES = {
    'thumb': [0, 1, 2, 3, 4],
    'index': [0, 5, 6, 7, 8],
    'middle': [0, 9, 10, 11, 12],
    'ring': [0, 13, 14, 15, 16],
    'pinky': [0, 17, 18, 19, 20]
}

def interpret_finger_angles(centroid):
    """
    Interpret the 16-element centroid as finger angles.
    
    Based on cluster.py's extract_finger_angles function:
    - 3 angles per finger (between consecutive segments) = 15 angles
    - 1 thumb abduction angle = 1 angle
    Total: 16 angles
    
    Args:
        centroid (list): 16 angle values in radians
        
    Returns:
        dict: Dictionary with finger names and their angles
    """
    if not centroid or len(centroid) != 16:
        return None
    
    angles = {}
    idx = 0
    
    # Extract 3 angles per finger
    for finger_name in ['thumb', 'index', 'middle', 'ring', 'pinky']:
        finger_angles = centroid[idx:idx+3]
        angles[finger_name] = {
            'joint1': finger_angles[0],  # First joint angle
            'joint2': finger_angles[1],  # Second joint angle  
            'joint3': finger_angles[2]   # Third joint angle
        }
        idx += 3
    
    # Last angle is thumb abduction
    angles['thumb_abduction'] = centroid[15]
    
    return angles

def visualize_finger_angles(centroid, hand_type='hand', save_path=None):
    """
    Create visualization of finger angles from centroid data.
    
    Args:
        centroid (list): List of 16 angle values
        hand_type (str): Type of hand ('l_hand' or 'r_hand')  
        save_path (str): Path to save the PNG file
    """
    angles = interpret_finger_angles(centroid)
    if not angles:
        print(f"Invalid centroid data. Expected 16 angles, got {len(centroid) if centroid else 0}")
        return
    
    # Convert angles to degrees for better readability
    finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    joint_names = ['joint1', 'joint2', 'joint3']
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Bar chart of all joint angles
    all_angles = []
    labels = []
    colors = []
    color_map = {'thumb': 'red', 'index': 'blue', 'middle': 'green', 'ring': 'orange', 'pinky': 'purple'}
    
    for finger in finger_names:
        for joint in joint_names:
            angle_deg = np.degrees(angles[finger][joint])
            all_angles.append(angle_deg)
            labels.append(f"{finger}\n{joint}")
            colors.append(color_map[finger])
    
    ax1.bar(range(len(all_angles)), all_angles, color=colors, alpha=0.7)
    ax1.set_xlabel('Finger Joints')
    ax1.set_ylabel('Angle (degrees)')
    ax1.set_title(f'{hand_type.capitalize()} - All Joint Angles')
    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Polar plot of finger curvature
    ax2 = plt.subplot(2, 2, 2, projection='polar')
    finger_curvatures = []
    theta_positions = []
    
    for i, finger in enumerate(finger_names):
        # Calculate average curvature per finger
        avg_angle = np.mean([angles[finger][joint] for joint in joint_names])
        finger_curvatures.append(avg_angle)
        theta_positions.append(i * 2 * np.pi / 5)  # Evenly space fingers
    
    ax2.bar(theta_positions, finger_curvatures, width=0.8, alpha=0.7, 
            color=[color_map[f] for f in finger_names])
    ax2.set_title(f'{hand_type.capitalize()} - Finger Curvature (Polar)')
    ax2.set_thetagrids([np.degrees(pos) for pos in theta_positions], finger_names)
    
    # Plot 3: Individual finger comparison
    x_pos = np.arange(len(joint_names))
    width = 0.15
    
    for i, finger in enumerate(finger_names):
        joint_angles_deg = [np.degrees(angles[finger][joint]) for joint in joint_names]
        ax3.bar(x_pos + i*width, joint_angles_deg, width, 
                label=finger, color=color_map[finger], alpha=0.7)
    
    ax3.set_xlabel('Joint Position')
    ax3.set_ylabel('Angle (degrees)')
    ax3.set_title(f'{hand_type.capitalize()} - Joint Angles by Finger')
    ax3.set_xticks(x_pos + width * 2)
    ax3.set_xticklabels(joint_names)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Hand pose summary with thumb abduction
    summary_data = {
        'Thumb Abduction': np.degrees(angles['thumb_abduction']),
        'Avg Thumb': np.degrees(np.mean([angles['thumb'][j] for j in joint_names])),
        'Avg Index': np.degrees(np.mean([angles['index'][j] for j in joint_names])),
        'Avg Middle': np.degrees(np.mean([angles['middle'][j] for j in joint_names])),
        'Avg Ring': np.degrees(np.mean([angles['ring'][j] for j in joint_names])),
        'Avg Pinky': np.degrees(np.mean([angles['pinky'][j] for j in joint_names]))
    }
    
    bars = ax4.bar(summary_data.keys(), summary_data.values(), 
                   color=['gray'] + [color_map[f] for f in finger_names], alpha=0.7)
    ax4.set_ylabel('Angle (degrees)')
    ax4.set_title(f'{hand_type.capitalize()} - Hand Pose Summary')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, summary_data.values()):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.1f}°', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Finger angles visualization saved to {save_path}")
    else:
        plt.show()
    
    plt.close()

def analyze_hand_pose(centroid, hand_type='hand'):
    """
    Analyze hand pose from centroid angles and provide interpretation.
    
    Args:
        centroid (list): List of 16 angle values
        hand_type (str): Type of hand ('l_hand' or 'r_hand')
        
    Returns:
        dict: Analysis results with pose interpretation
    """
    angles = interpret_finger_angles(centroid)
    if not angles:
        return None
    
    # Convert to degrees for analysis
    finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    analysis = {
        'hand_type': hand_type,
        'finger_analysis': {},
        'overall_pose': {}
    }
    
    total_curvature = 0
    extended_fingers = 0
    bent_fingers = 0
    
    for finger in finger_names:
        joint_angles_deg = [np.degrees(angles[finger][joint]) for joint in ['joint1', 'joint2', 'joint3']]
        avg_angle = np.mean(joint_angles_deg)
        max_angle = np.max(joint_angles_deg)
        min_angle = np.min(joint_angles_deg)
        
        # Classify finger state (rough heuristic)
        if avg_angle < 30:
            state = "extended"
            extended_fingers += 1
        elif avg_angle > 120:
            state = "highly_bent"
            bent_fingers += 1
        elif avg_angle > 60:
            state = "bent"
            bent_fingers += 1
        else:
            state = "slightly_bent"
        
        analysis['finger_analysis'][finger] = {
            'average_angle': avg_angle,
            'max_angle': max_angle,
            'min_angle': min_angle,
            'state': state,
            'joint_angles': joint_angles_deg
        }
        
        total_curvature += avg_angle
    
    # Thumb abduction analysis
    thumb_abduction_deg = np.degrees(angles['thumb_abduction'])
    
    # Overall pose classification
    analysis['overall_pose'] = {
        'total_curvature': total_curvature,
        'average_curvature': total_curvature / 5,
        'extended_fingers': extended_fingers,
        'bent_fingers': bent_fingers,
        'thumb_abduction': thumb_abduction_deg,
        'pose_classification': classify_hand_pose(extended_fingers, bent_fingers, thumb_abduction_deg)
    }
    
    return analysis

def classify_hand_pose(extended_fingers, bent_fingers, thumb_abduction):
    """Simple pose classification based on finger states."""
    if extended_fingers >= 4:
        return "open_hand"
    elif bent_fingers >= 4:
        if thumb_abduction < 30:
            return "closed_fist"
        else:
            return "loose_fist"
    elif extended_fingers == 1:
        return "pointing"
    elif extended_fingers == 2:
        return "peace_sign_or_two_fingers"
    elif extended_fingers == 3:
        return "three_fingers"
    else:
        return "partial_gesture"

def angles_to_approximate_keypoints(angles):
    """
    Convert 16 finger angles back to approximate 3D keypoints for visualization.
    
    Args:
        angles (list): 16 angle values representing finger poses
        
    Returns:
        list: 21 keypoints, each with [x, y, z] coordinates
    """
    if not angles or len(angles) != 16:
        return None
    
    # Create base hand structure with normalized proportions
    keypoints = np.zeros((21, 3))
    
    # Wrist at origin
    keypoints[0] = [0, 0, 0]
    
    # Base finger lengths (normalized)
    finger_lengths = {
        'thumb': [0.08, 0.06, 0.05, 0.04],
        'index': [0.10, 0.08, 0.06, 0.05],
        'middle': [0.12, 0.09, 0.07, 0.06],
        'ring': [0.11, 0.08, 0.06, 0.05],
        'pinky': [0.08, 0.06, 0.05, 0.04]
    }
    
    # Base positions for finger roots relative to wrist
    finger_roots = {
        'thumb': [-0.03, 0.02, 0],
        'index': [-0.02, 0.08, 0],
        'middle': [0, 0.09, 0],
        'ring': [0.02, 0.08, 0],
        'pinky': [0.04, 0.06, 0]
    }
    
    angle_idx = 0
    finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    
    for finger_name in finger_names:
        indices = FINGER_INDICES[finger_name]
        root_pos = np.array(finger_roots[finger_name])
        lengths = finger_lengths[finger_name]
        
        # Get the 3 angles for this finger
        finger_angles = angles[angle_idx:angle_idx+3]
        angle_idx += 3
        
        # Start from root position
        keypoints[indices[0]] = root_pos
        
        # Build finger segment by segment
        current_pos = root_pos.copy()
        current_direction = np.array([0, 1, 0])  # Initial direction (up)
        
        for i in range(1, len(indices)):
            segment_length = lengths[i-1]
            
            if i-1 < len(finger_angles):
                # Apply bending angle
                bend_angle = finger_angles[i-1]
                
                # Create rotation matrix for bending (around Z-axis)
                cos_a, sin_a = np.cos(bend_angle), np.sin(bend_angle)
                rotation_matrix = np.array([
                    [cos_a, -sin_a, 0],
                    [sin_a, cos_a, 0],
                    [0, 0, 1]
                ])
                
                # Rotate direction vector
                current_direction = rotation_matrix @ current_direction
            
            # Move to next joint
            current_pos += current_direction * segment_length
            keypoints[indices[i]] = current_pos.copy()
    
    # Apply thumb abduction (last angle)
    if len(angles) > 15:
        thumb_abduction = angles[15]
        # Rotate thumb around Y-axis for abduction
        cos_ab, sin_ab = np.cos(thumb_abduction), np.sin(thumb_abduction)
        abduction_matrix = np.array([
            [cos_ab, 0, sin_ab],
            [0, 1, 0],
            [-sin_ab, 0, cos_ab]
        ])
        
        # Apply abduction to thumb keypoints
        for i in FINGER_INDICES['thumb']:
            if i > 0:  # Don't move the root
                relative_pos = keypoints[i] - keypoints[0]
                rotated_pos = abduction_matrix @ relative_pos
                keypoints[i] = keypoints[0] + rotated_pos
    
    # Center the hand and add some variation for better visualization
    center = keypoints.mean(axis=0)
    keypoints -= center
    
    # Scale to reasonable size
    keypoints *= 3.0
    
    # Return as list of [x,y,z] coordinates for each keypoint
    return [[float(x), float(y), float(z)] for x, y, z in keypoints]

def keypoints_to_3d_visualization(centroid):
    """
    Convert 60-element root-translated keypoint centroid back to 21x3 keypoints for visualization.
    
    Args:
        centroid (list): 60 values representing 20 keypoints × 3 coordinates (wrist excluded)
        
    Returns:
        list: 21 keypoints with [x, y, z] coordinates (wrist at origin)
    """
    if not centroid or len(centroid) != 60:
        return None
    
    # Reshape 60-element vector back to 20x3 keypoints
    keypoints_rel = np.array(centroid).reshape(20, 3)
    
    # Create full 21x3 array with wrist at origin
    keypoints = np.zeros((21, 3))
    keypoints[0] = [0, 0, 0]  # Wrist at origin
    keypoints[1:] = keypoints_rel  # Other 20 keypoints
    
    # Return as list of [x,y,z] coordinates for each keypoint
    return [[float(x), float(y), float(z)] for x, y, z in keypoints]

def analyze_keypoint_pose(centroid, hand_type='hand'):
    """
    Analyze hand pose from 60-dimensional keypoint centroid.
    
    Args:
        centroid (list): List of 60 values (20 keypoints × 3 coordinates)
        hand_type (str): Type of hand ('l_hand' or 'r_hand')
        
    Returns:
        dict: Analysis results with pose interpretation
    """
    keypoints_3d = keypoints_to_3d_visualization(centroid)
    if not keypoints_3d:
        return None
    
    keypoints = np.array(keypoints_3d)
    
    # Calculate basic hand metrics
    analysis = {
        'hand_type': hand_type,
        'keypoint_analysis': {},
        'overall_pose': {}
    }
    
    # Calculate finger spreads and extensions
    finger_tips = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky tips
    finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    
    extended_fingers = 0
    total_extension = 0
    
    for i, (tip_idx, finger_name) in enumerate(zip(finger_tips, finger_names)):
        # Distance from wrist to fingertip
        tip_distance = np.linalg.norm(keypoints[tip_idx] - keypoints[0])
        
        # Distance from base to tip for extension measure
        base_indices = FINGER_INDICES[finger_name]
        base_to_tip = np.linalg.norm(keypoints[tip_idx] - keypoints[base_indices[1]])
        
        # Simple extension heuristic
        if tip_distance > 0.15:  # Adjust threshold as needed
            extended_fingers += 1
        
        analysis['keypoint_analysis'][finger_name] = {
            'tip_distance_from_wrist': float(tip_distance),
            'base_to_tip_distance': float(base_to_tip),
            'tip_position': keypoints[tip_idx].tolist()
        }
        
        total_extension += tip_distance
    
    # Overall hand spread
    hand_span = np.linalg.norm(keypoints[4] - keypoints[20])  # Thumb to pinky
    hand_length = np.linalg.norm(keypoints[12] - keypoints[0])  # Middle finger to wrist
    
    analysis['overall_pose'] = {
        'extended_fingers': extended_fingers,
        'average_extension': float(total_extension / 5),
        'hand_span': float(hand_span),
        'hand_length': float(hand_length),
        'pose_classification': classify_keypoint_pose(extended_fingers, hand_span, hand_length)
    }
    
    return analysis

def classify_keypoint_pose(extended_fingers, hand_span, hand_length):
    """Simple pose classification based on keypoint metrics."""
    if extended_fingers >= 4 and hand_span > 0.2:
        return "open_hand"
    elif extended_fingers <= 1 and hand_span < 0.1:
        return "closed_fist"
    elif extended_fingers == 1:
        return "pointing"
    elif extended_fingers == 2:
        return "peace_sign_or_two_fingers"
    elif extended_fingers == 3:
        return "three_fingers"
    else:
        return "partial_gesture"

if __name__ == "__main__":
    # Create visualizations directory if it doesn't exist
    visualizations_dir = '/web/hamer_server/visualizations'
    os.makedirs(visualizations_dir, exist_ok=True)
    
    # Read the JSON file content
    with open('/web/gebarenoverleg_media/studioFilesMini/raw/angle_hand_clusters.json', 'r') as file:
        json_content = file.read()
    
    result = find_top_n_counts_from_string(json_content, 50)
    print("Top 50 highest count ids from file:")
    
    # Convert angle centroids to keypoints for visualization compatibility
    for hand, data_list in result.items():
        print(f"\n{hand.upper()}:")
        for i, data in enumerate(data_list, 1):
            print(f"  {i}. ID {data['id']} with count {data['count']}")
            
            # Show first few member files for verification
            if data.get('members') and len(data['members']) > 0:
                member_files = list(set([member['file'] for member in data['members'][:5]]))
                print(f"    Sample files: {', '.join(member_files)}")
            
            # Handle keypoint centroid (60 dimensions)
            if data.get('centroid') and len(data['centroid']) == 60:
                # Store original keypoint data
                original_keypoints = data['centroid'].copy()
                
                # Convert to 3D keypoints for visualization
                keypoints_3d = keypoints_to_3d_visualization(data['centroid'])
                if keypoints_3d:
                    # Replace with 3D keypoints for visualization
                    data['centroid'] = keypoints_3d
                    print(f"    Converted 60D keypoints to {len(keypoints_3d)} 3D keypoints for visualization")
                
                # Analyze pose from original keypoint data
                pose_analysis = analyze_keypoint_pose(original_keypoints, hand)
                if pose_analysis:
                    overall = pose_analysis['overall_pose']
                    print(f"    Pose: {overall['pose_classification']}")
                    print(f"    Extended fingers: {overall['extended_fingers']}")
                    print(f"    Hand span: {overall['hand_span']:.3f}")
                    print(f"    Hand length: {overall['hand_length']:.3f}")
            elif data.get('centroid') and len(data['centroid']) == 16:
                # Legacy angle-based centroids - convert to keypoints
                original_angles = data['centroid'].copy()
                keypoints = angles_to_approximate_keypoints(data['centroid'])
                if keypoints:
                    data['centroid'] = keypoints
                    print(f"    Converted 16 angles to {len(keypoints)} keypoints for 3D visualization")
                
                pose_analysis = analyze_hand_pose(original_angles, hand)
                if pose_analysis:
                    overall = pose_analysis['overall_pose']
                    print(f"    Pose: {overall['pose_classification']} (from angles)")
                    print(f"    Average curvature: {overall['average_curvature']:.1f}°")
            elif data.get('centroid'):
                print(f"    Warning: Unexpected centroid length: {len(data['centroid'])} (expected 60 for keypoints or 16 for angles)")
    
    # Save results to JSON file  
    output_file = '/web/hamer_server/top50_hand_clusters.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nTop 50 results saved to {output_file}")
    print("Centroids converted from angles to keypoints for 3D visualization compatibility")
    
    # Verify JSON structure for top50.html compatibility
    print("\nVerifying JSON structure for top50.html compatibility...")
    for hand, clusters in result.items():
        if clusters:
            first_cluster = clusters[0]
            required_fields = ['id', 'count', 'centroid', 'members']
            missing_fields = [field for field in required_fields if field not in first_cluster]
            if missing_fields:
                print(f"WARNING: {hand} clusters missing fields: {missing_fields}")
            else:
                print(f"✓ {hand} clusters have all required fields")
                
                # Check centroid format
                if first_cluster['centroid'] and len(first_cluster['centroid']) == 21:
                    # Check if each keypoint has 3 coordinates
                    if all(len(kp) == 3 for kp in first_cluster['centroid']):
                        print(f"✓ {hand} centroids have 21 keypoints with 3D coordinates")
                    else:
                        print(f"WARNING: {hand} keypoints don't all have 3 coordinates")
                else:
                    print(f"WARNING: {hand} centroids have {len(first_cluster['centroid']) if first_cluster['centroid'] else 0} elements, expected 21")
                
                # Check members format
                if first_cluster['members']:
                    member_fields = ['file', 'frame']
                    first_member = first_cluster['members'][0]
                    missing_member_fields = [field for field in member_fields if field not in first_member]
                    if missing_member_fields:
                        print(f"WARNING: {hand} member objects missing fields: {missing_member_fields}")
                    else:
                        print(f"✓ {hand} member objects have all required fields")