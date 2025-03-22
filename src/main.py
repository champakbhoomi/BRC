import math
import mmap
import multiprocessing

def round_inf(x):
    return math.ceil(x * 10) / 10  

def process_chunk(filename, start_offset, end_offset):
    # Use a plain dictionary to hold city data: [min, max, total, count]
    data = {}
    with open(filename, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        size = len(mm)
        
        # Move start_offset to next newline if not at file beginning
        if start_offset != 0:
            while start_offset < size and mm[start_offset] != ord('\n'):
                start_offset += 1
            start_offset += 1
        
        # Extend end_offset to cover the full line
        end = end_offset
        while end < size and mm[end] != ord('\n'):
            end += 1
        if end < size:
            end += 1
        
        chunk = mm[start_offset:end]
        mm.close()
    
    # Process each line using splitlines() for speed
    for line in chunk.splitlines():
        if not line:
            continue
        
        # Use partition to separate the two fields
        city, sep, score_str = line.partition(b';')
        if sep != b';':
            continue
        
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        # Update the city entry in the dictionary
        if city in data:
            stats = data[city]
            if score < stats[0]:
                stats[0] = score
            if score > stats[1]:
                stats[1] = score
            stats[2] += score
            stats[3] += 1
        else:
            data[city] = [score, score, score, 1]
    
    return data

def merge_data(data_list):
    final = {}
    for data in data_list:
        for city, stats in data.items():
            if city in final:
                final_stats = final[city]
                if stats[0] < final_stats[0]:
                    final_stats[0] = stats[0]
                if stats[1] > final_stats[1]:
                    final_stats[1] = stats[1]
                final_stats[2] += stats[2]
                final_stats[3] += stats[3]
            else:
                final[city] = stats.copy()
    return final

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    # Determine file size using mmap for efficiency
    with open(input_file_name, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        file_size = len(mm)
        mm.close()
    
    num_procs = multiprocessing.cpu_count() * 2  
    chunk_size = file_size // num_procs
    chunks = [(i * chunk_size, (i + 1) * chunk_size if i < num_procs - 1 else file_size)
              for i in range(num_procs)]
    
    with multiprocessing.Pool(num_procs) as pool:
        tasks = [(input_file_name, start, end) for start, end in chunks]
        results = pool.starmap(process_chunk, tasks)
    
    final_data = merge_data(results)
    
    out = []
    # Sort the output lines alphabetically by city name
    for city in sorted(final_data.keys(), key=lambda c: c.decode()):
        mn, mx, total, count = final_data[city]
        avg = round_inf(total / count)
        out.append(f"{city.decode()}={round_inf(mn):.1f}/{avg:.1f}/{round_inf(mx):.1f}\n")
    
    with open(output_file_name, "w") as f:
        f.writelines(out)

if __name__ == "__main__":
    main()