# Bee Health Monitor project

The aim of this project is to design an open-source project, which would be done from commonly available modules using 3D printing technology.

## Which device is presented there?

This is a second version of the bee health monitor device, which was developed after evaluating the initial measurements with the original device. This version is designed to be realised by anyone at home with commonly available tools, hardware, and a 3D printer. The recommended print material is PETG or ASA as it provides good sunlight and weather durability and can be easily sterilised when moved to the other bee hive. The entire construction is made out of 6 printable parts and a single 2mm plexiglass. An acrylic varnish is applied to improve the water resistance. Using this device, dataset [Bee Dataset BUT-2](https://www.kaggle.com/datasets/imonbilk/bee-dataset-but-2) was collected. This device mounted on the beehive is shown in figure bellow:

![Second version of *Bee health monitor* device](https://github.com/boortel/Bee-Health-Monitor/assets/33236294/0c7f2f24-1383-4c0c-b31d-8bd1ebd28ba8)

The chassis is mentioned to be mounted directly on the entrance to the hive in the way, so the bees are forced to use the 8mm long tunnels on the bottom of the device. The camera field of view is illuminated by a diffused warm white LED. The camera periodically senses bees when passing through the tunnels, as shown in figure bellow:

![Sample from the image part of the dataset BUT-2.](https://github.com/boortel/Bee-Health-Monitor/assets/33236294/e88572ed-5762-4480-afc2-33d8426aa35e)

The internal electronics consist of commonly available hobby electronic parts and RaspberryPi 4 as a control unit. The sensor equipment consists out of a camera, microphone, two humidity and temperature sensors intend to be placed inside the beehive, CO2 sensor, light sensor and an temperature, humidity and atmospheric pressure sensor to be positioned outside. All data are stored on an internal USB drive in a set interval, and the number of incoming and outgoing bees is evaluated from the camera capture. The main specifications of this device are shown in table bellow:

![Device parameters.](https://github.com/boortel/Bee-Health-Monitor/assets/33236294/a0a61f70-94d6-484c-8911-814e23cfc0b6)

## Related research papers

Besides the *Bee Health Monitor* platform, we would like to present our bee related research:

- Bee datasets
  - [Bee Dataset BUT-1](https://www.kaggle.com/datasets/imonbilk/bee-dataset-but-1): dataset collected with the first generation of our device. It contains only image data.
  - [Bee Dataset BUT-2](https://www.kaggle.com/datasets/imonbilk/bee-dataset-but-2): dataset collected with the second generation of our device. It contains image, sound and sensor data.
  - [Bee Dataset BUT-HS](https://www.kaggle.com/datasets/imonbilk/bee-dataset-but-hs): hyperspectral dataset containing images of bees, Varroa mites and detritus.
 
- Research papers
  -  [Visual Diagnosis of the Varroa Destructor Parasitic Mite in Honeybees Using Object Detector Techniques](https://www.mdpi.com/1424-8220/21/8/2764): article describing the Varroa mite detection using the YOLOv5 network.
  -  [Raspberry Pi Bee Health Monitoring Device](https://arxiv.org/abs/2304.14444): paper describing the communication and remote logging of the *Bee health monitor device*.
  -  [Machine learning and computer vision techniques in continuous beehive monitoring applications: A survey](https://www.sciencedirect.com/science/article/pii/S0168169923009481?dgcid=author): survey article focusing on the visual based bee health monitoring methods. A full version of the paper has a restricted access, a free preprint is available [here](https://arxiv.org/abs/2208.00085).
  -  [Computer Vision Approaches for Automated Bee Counting Application](https://www.sciencedirect.com/science/article/pii/S2405896324004580): paper comparing three possible approaches in the bee counting.
  -  [Varroa destructor detection on honey bees using hyperspectral imagery](https://www.sciencedirect.com/science/article/pii/S0168169924006100?dgcid=rss_sd_all): article describing a possible use of the hypespectral imaging in Varroa mite detection.
 
- Final thesis
  - [Approximation of functions determining colony activity using neural networks](https://www.vut.cz/studenti/zav-prace/detail/151629): Thesis describing the development of the setup presented in paper *Raspberry Pi Bee Health Monitoring Device* in a more detail together with further clustering experiments.

## Software

The complete overview of the used software is provided in [software](https://github.com/boortel/Bee-Health-Monitor/tree/main/software) section.

## Hardware

The complete overview of device 3D printing, laser cutting, assembly and inner electrical installation is provided in [hardware](https://github.com/boortel/Bee-Health-Monitor/tree/main/hardware) section.

### Keywords

Bees, Health, Camera, Sensory, Neural Networks, AI
